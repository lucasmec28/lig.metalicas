import json
import hashlib
from dataclasses import replace
import streamlit as st
import pandas as pd
from lro.models import Connection,Profile,profiles,STEELS,BOLTS,DIAMETERS,THICKNESSES,KGF,VERSION
from lro.engine import evaluate
from lro.examples import presets
from lro.drawing import image_bytes
from lro.report import create_report,display,number,BRAND,LINK
from lro.benchmarks import benchmarks

st.set_page_config(page_title='LRO Ligações',page_icon='🔩',layout='wide')
st.markdown('''<style>
 .block-container {padding-top:2rem;max-width:1500px}
 [data-testid="stMetricValue"] {font-size:1.65rem}
 h1 {letter-spacing:-.045em!important;font-weight:750!important}
 .eyebrow {font-size:.78rem;letter-spacing:.16em;color:#397895;font-weight:700}
 .muted {color:#65798a;font-size:.95rem;line-height:1.5}
 [data-testid="stSidebar"] {background:#f3f6f8}
 div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:12px}
 </style>''',unsafe_allow_html=True)

P=profiles();PRESETS=presets()


def seed(c):
    state=st.session_state
    for key,value in c.__dict__.items():
        if key not in ('beam','support','V','N'):state[key]=value
    state['V_kgf']=c.V/KGF;state['N_kgf']=c.N/KGF
    state['center_plate']=abs(c.plate_top-(c.beam.d-c.hp)/2)<1e-6
    state['db_label']=next(k for k,v in DIAMETERS.items() if abs(c.db-v)<1e-6)
    state['tp_label']=next((k for k,v in THICKNESSES.items() if abs(c.tp-v)<1e-6),'5/16"')
    state['custom_t']=not any(abs(c.tp-v)<1e-6 for v in THICKNESSES.values());state['real_t']=c.tp
    for prefix,p in [('beam',c.beam),('support',c.support)]:
        state[prefix+'_name']=p.name if p.name in P else 'Seção I personalizada'
        for key in ['d','bf','tw','tf','clear']:state[prefix+'_'+key]=float(getattr(p,key))
        state[prefix+'_manual_name']=p.name
    state.pop('report',None)


def load_example():seed(PRESETS[st.session_state['example']])


def import_file():
    # O callback executa antes da criação dos widgets, evitando alterar suas
    # chaves depois de instanciados no mesmo ciclo do Streamlit.
    try:
        uploaded=st.session_state.project_upload
        if uploaded is None:raise ValueError('Selecione um arquivo de projeto.')
        if len(uploaded.getvalue())>200_000:raise ValueError('Arquivo maior que o limite de projeto.')
        imported=Connection.from_dict(json.loads(uploaded.getvalue()))
        ir=evaluate(imported)
        if any(x.severity=='error' for x in ir.issues):raise ValueError('; '.join(x.text for x in ir.issues if x.severity=='error'))
        seed(imported)
        st.session_state.pop('import_error',None)
    except (ValueError,TypeError,KeyError,OverflowError) as exc:
        st.session_state['import_error']='Não foi possível abrir: '+str(exc)


if 'beam_name' not in st.session_state:seed(next(iter(PRESETS.values())))


def profile_changed(prefix):
    name=st.session_state[prefix+'_name']
    if name in P:
        p=P[name]
        st.session_state[prefix+'_steel']='ASTM A36' if p.family in ('CS','CVS','VS') else 'ASTM A572 Gr.50'


def profile_widget(prefix,label):
    name=st.selectbox(label,['Seção I personalizada']+list(P),key=prefix+'_name',on_change=profile_changed,args=(prefix,))
    if name in P:return P[name]
    with st.expander('Dimensões da seção personalizada',expanded=True):
        name=st.text_input('Designação',key=prefix+'_manual_name')
        cols=st.columns(2)
        vals={}
        for i,(key,text) in enumerate([('d','Altura d'),('bf','Largura bf'),('tw','Alma tw'),('tf','Mesa tf'),('clear','Altura livre sem concordâncias')]):
            with cols[i%2]:vals[key]=st.number_input(text+' (mm)',min_value=.1,max_value=3000.,key=prefix+'_'+key)
        area=2*vals['bf']*vals['tf']+(vals['d']-2*vals['tf'])*vals['tw']
        return Profile(name,'Soldado',max(area,1)*.00785,area=max(area,1),**vals)


with st.sidebar:
    st.markdown('<div class="eyebrow">LRO · ENGENHARIA</div>',unsafe_allow_html=True)
    st.title('Ligações')
    st.caption(f'Versão {VERSION} · pré-verificação técnica')
    st.text_input('Projeto ou identificação',key='project')
    st.selectbox('Carregar exemplo',list(PRESETS),key='example')
    st.button('Usar este exemplo',on_click=load_example,width='stretch')
    with st.expander('Abrir projeto salvo'):
        uploaded=st.file_uploader('Arquivo JSON do LRO Ligações',type=['json'],key='project_upload')
        st.button('Abrir arquivo',disabled=uploaded is None,on_click=import_file)
        if 'import_error' in st.session_state:st.error(st.session_state.import_error)
    st.divider()
    st.caption('Nesta versão')
    st.markdown('**Single plate**\n\nViga–viga e viga–mesa de pilar. Um caso de esforços já majorados.')
    with st.expander('Próximas ligações'):
        st.write('Cantoneira simples e dupla cantoneira. Depois, enrijecedores, múltiplas vigas no nó e demais famílias.')
    st.link_button('LinkedIn · Lucas Oliveira',LINK,width='stretch')

st.markdown('<div class="eyebrow">LIGAÇÕES DE AÇO</div>',unsafe_allow_html=True)
st.title('Single plate')
st.markdown('<p class="muted">Escolha os perfis, ajuste o detalhe e acompanhe as verificações. A memória usa os mesmos dados e o mesmo desenho.</p>',unsafe_allow_html=True)

left,right=st.columns([1,1.65],gap='large')
with left:
    with st.container(border=True):
        st.subheader('1 · Ligação e esforços')
        st.selectbox('Tipo de apoio',['beam_web','column_flange'],format_func=lambda x:'Alma de viga — viga a 90°' if x=='beam_web' else 'Mesa de pilar — alinhada à alma',key='kind')
        beam=profile_widget('beam','Viga apoiada')
        support=profile_widget('support','Perfil de apoio')
        loads=st.columns(2)
        with loads[0]:vk=st.number_input('Cortante Vd (kgf)',min_value=-1.e7,max_value=1.e7,key='V_kgf',format='%.3f')
        with loads[1]:nk=st.number_input('Tração Nd (kgf)',min_value=0.,max_value=1.e7,key='N_kgf',format='%.3f')
        st.caption(f'{vk*KGF/1000:.3f} kN de cortante · {nk*KGF/1000:.3f} kN de tração. Entrada já majorada.')
    with st.container(border=True):
        st.subheader('2 · Detalhamento')
        cols=st.columns(2)
        with cols[0]:
            st.selectbox('Parafuso Ø (pol.)',list(DIAMETERS),key='db_label')
            st.number_input('Número de parafusos',2,12,key='n',step=1)
            st.number_input('Passo p (mm)',min_value=1.,max_value=400.,key='pitch')
            st.number_input('Borda vertical eᵥ (mm)',min_value=1.,max_value=200.,key='edge_v')
            st.number_input('Face → parafusos a (mm)',min_value=10.,max_value=1000.,key='a')
        with cols[1]:
            st.selectbox('Chapa tₚ (pol.)',list(THICKNESSES),key='tp_label')
            st.number_input('Filete de solda w (mm)',min_value=1.,max_value=25.,key='weld')
            st.number_input('Borda livre eₕ (mm)',min_value=1.,max_value=200.,key='edge_h')
            st.number_input('Face → ponta da viga g (mm)',min_value=1.,max_value=900.,key='gap')
        with st.expander('Posição da chapa e recortes'):
            centered=st.checkbox('Centralizar chapa na altura da viga',key='center_plate')
            if not centered:st.number_input('Topo da chapa a partir do topo da viga (mm)',0.,2000.,key='plate_top')
            if st.session_state.kind=='beam_web':st.number_input('Topo da viga apoiada abaixo do apoio (mm)',-1500.,1500.,key='beam_level')
            st.selectbox('Recorte',['none','top','both'],format_func=lambda x:{'none':'Sem recorte','top':'Mesa superior','both':'Mesas superior e inferior'}[x],key='cope')
            if st.session_state.cope!='none':
                st.caption('A V1 verifica a geometria e mantém a verificação estrutural do recorte como pendência.')
                st.number_input('Comprimento do recorte (mm)',1.,1000.,key='cope_length')
                st.number_input('Profundidade superior (mm)',1.,1000.,key='cope_top')
                if st.session_state.cope=='both':st.number_input('Profundidade inferior (mm)',1.,1000.,key='cope_bottom')
        with st.expander('Montagem e hipóteses'):
            st.checkbox('Contenção eficaz contra rotação longitudinal da viga confirmada',key='restrained',help='Uma laje ou outro sistema deve efetivamente fornecer essa contenção. Marcar exige confirmação do detalhe real.')
            st.number_input('Folga mínima entre peças (mm)',0.,50.,key='clearance')
            st.number_input('Raio do envelope de montagem (mm)',1.,80.,key='tool_radius',help='Envelope de porca, arruela e ferramenta. Valor inicial ilustrativo, ajustável ao sistema de montagem.')
            st.checkbox('Furos executados com broca',key='drilled',help='Retira o acréscimo de 2 mm no desconto da seção líquida, conforme 5.2.4.')
            st.checkbox('Borda da solda com execução reforçada especificada',key='reinforced_weld')
            st.checkbox('Verificar mínimo normativo de 45 kN',key='norm_minimum')
            st.checkbox('Informar espessura real da chapa',key='custom_t')
            if st.session_state.custom_t:st.number_input('Espessura real tₚ (mm)',1.,50.,key='real_t',format='%.4f')
    with st.expander('Materiais e especificações'):
        st.selectbox('Aço da viga',list(STEELS),key='beam_steel')
        st.selectbox('Aço do apoio',list(STEELS),key='support_steel')
        st.selectbox('Aço da chapa',[s.name for s in STEELS.values() if s.plate_allowed],key='plate_steel')
        st.selectbox('Especificação dos parafusos',list(BOLTS),key='bolt')
        st.checkbox('Rosca no plano de corte',key='threads')
        st.selectbox('Resistência do eletrodo fw (MPa)',[415.,485.,550.],key='fw')
        st.text_area('Observações do detalhe',key='notes')

state=st.session_state
hp=2*state.edge_v+(state.n-1)*state.pitch
top=(beam.d-hp)/2 if state.center_plate else state.plate_top
base=next(iter(PRESETS.values()))
kwargs={k:state[k] for k in base.__dict__ if k in state and k not in ('beam','support','V','N','db','tp','plate_top')}
c=Connection(beam=beam,support=support,V=vk*KGF,N=nk*KGF,db=DIAMETERS[state.db_label],tp=state.real_t if state.custom_t else THICKNESSES[state.tp_label],plate_top=top,**kwargs)
r=evaluate(c)
payload=json.dumps(c.to_dict(),ensure_ascii=False,indent=2,allow_nan=False)
digest=hashlib.sha256(payload.encode()).hexdigest()

@st.cache_data(show_spinner=False,max_entries=25)
def drawing_cached(raw,fmt):return image_bytes(Connection.from_dict(json.loads(raw)),fmt)

with right:
    with st.container(border=True):
        st.subheader('3 · Geometria e resultado')
        if r.geometry:
            st.image(drawing_cached(payload,'png'),width='stretch')
        if r.status=='GEOMETRIA INVÁLIDA':st.error(r.status)
        elif r.status=='NÃO ATENDE':st.error(r.status+' · revisar os itens com índice > 1')
        elif r.status=='VERIFICAÇÃO INCOMPLETA':st.warning(r.status)
        else:st.success(r.status)
        ms=st.columns(3)
        ms[0].metric('Chapa (mm)',f'{c.width:g} × {c.hp:g}',f't = {c.tp:.3f} mm',delta_color='off')
        ms[1].metric('Momento local de entrada',f'{(abs(c.V)*c.a+abs(c.N*c.eccentric_n))/(KGF*1000):.2f}','kgf·m',delta_color='off')
        ms[2].metric('Índice determinante',number(r.governing.ratio,3) if r.governing else '—')
        st.caption(f'Furo padrão Ø {c.dh:.4f} mm · {c.beam_steel} / {c.support_steel} / chapa {c.plate_steel}')
        if r.governing:st.caption('Determina: '+r.governing.name+' · '+r.governing.case)
        for issue in r.issues:
            f=st.error if issue.severity=='error' else st.warning if issue.severity=='pending' else st.info
            f(issue.text+'  ['+issue.reference+']')
        if r.checks:
            st.caption('Todos os índices exibidos abaixo incluem o mínimo normativo quando aplicável. Um índice ≤ 1 não elimina pendências de escopo.')
    with st.container(border=True):
        st.subheader('4 · Salvar e exportar')
        detailed=st.checkbox('Memória detalhada',value=False,help='A compacta desenvolve os itens determinantes por componente; todas as verificações aparecem no quadro resumo.')
        if st.button('Gerar memória Word',type='primary',disabled=not bool(r.checks),width='stretch'):
            with st.spinner('Preparando imagem, equações e memória...'):
                state['report']=(digest,detailed,create_report(c,r,detailed))
        if 'report' in state and state.report[:2]==(digest,detailed):
            st.download_button('Baixar memória .docx',state.report[2],file_name='Memoria_LRO_single_plate.docx',mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',width='stretch')
        files=st.columns(2)
        files[0].download_button('Salvar projeto',payload,file_name='Projeto_LRO_ligacao.json',mime='application/json',width='stretch')
        if r.geometry:files[1].download_button('Desenho vetorial SVG',drawing_cached(payload,'svg'),file_name='Ligacao_LRO.svg',mime='image/svg+xml',width='stretch')

tabs=st.tabs(['Verificações','Equações e referências','Validação','Escopo da versão'])
with tabs[0]:
    if r.checks:
        table_rows=[]
        for x in r.checks:
            sd,u=display(x.demand,x.unit);rd,_=display(x.resistance,x.unit)
            table_rows.append({'Verificação':x.name,'Sd':sd,'Rd':rd,'Unidade':u,'Índice':round(x.ratio,5),'Resultado':'Atende' if x.passed else 'Não atende'})
        st.dataframe(pd.DataFrame(table_rows),hide_index=True,width='stretch',column_config={'Índice':st.column_config.NumberColumn(format='%.3f')})
    else:st.info('Corrija os dados para calcular as resistências.')
with tabs[1]:
    for x in r.checks:
        with st.expander(x.name):
            st.write(x.equation);st.write(x.substitution);st.write(x.variables);st.caption(x.reference)
    st.caption('O Word contém equações editáveis. Os procedimentos complementares AISC/SCI são identificados; as tabelas LRFD não são convertidas em bloco para NBR.')
with tabs[2]:
    vals=benchmarks();st.metric('Conferências pontuais contra exemplos',f"{sum(v['atende'] for v in vals)} / {len(vals)}")
    st.dataframe(pd.DataFrame(vals),hide_index=True,width='stretch')
    st.info('Estas conferências validam componentes identificados, não a reprodução integral de todos os exemplos. No app usa-se e=a, inclusive em corte puro. O Carini original usa e=a/2 no grupo convencional; a comparação acima preserva essa hipótese apenas no teste. A NBR atual adota 0,45 e fub=830 MPa para A325; o exemplo antigo usa 0,40 e 825 MPa.')
with tabs[3]:
    st.markdown('''**Incluído:** single plate, uma coluna de 2–12 parafusos, cortante e tração, parafusos por contato, furos padrão, dois filetes de oficina, desenho proporcional, importação e exportação de projeto e memória Word.

**Conclusão condicionada:** alma da viga de apoio sob tração fora do plano, recortes, ausência de contenção eficaz nos casos indicados, solda mesa–alma de pilares soldados e detalhes fora das condições de ductilidade verificadas. Essas situações aparecem como pendências.

**Expansão seguinte:** cantoneiras simples e duplas; enrijecedores e duas vigas no nó; mais casos de esforços. O material recebido fica referenciado no documento de metodologia que acompanha o código.

O P902-23W contém tabelas complementares; suas tabelas 10-A/10-B são para paredes de perfis tubulares e não são aplicadas às almas dos perfis I desta versão.''')
st.divider()
st.caption(BRAND)
st.link_button('Contato no LinkedIn',LINK)
