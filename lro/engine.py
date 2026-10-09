"""Single plate em corte simples. Procedimentos e limites em docs/METODOLOGIA.md.

NBR 8800:2024 + errata 2025 para resistências. AISC/Carini são complementos
identificados, nunca tabelas LRFD convertidas por um fator global.
"""
import math
from dataclasses import replace
from .models import Connection, Check, Issue, Result, STEELS, BOLTS, DIAMETERS

G1, G2, E = 1.10, 1.35, 200000.0
NBR = "ABNT NBR 8800:2024, versão corrigida 2025"


def bolt_shear(db, fub, threads=True, gamma=G2):
    return (0.45 if threads else 0.56)*math.pi*db**2/4*fub/gamma


def elastic_bolts(n, pitch, V, N, M):
    """Forças resistentes do grupo, coordenadas y positivas para cima."""
    ys=[(i-(n-1)/2)*pitch for i in range(n)]
    J=sum(y*y for y in ys)
    if J<=0:raise ValueError("O grupo precisa de pelo menos dois parafusos distintos.")
    return [(N/n-M*y/J, V/n) for y in ys]


def bearing(db, dh, edge, pitch, t, fu):
    lc=max(0,min(edge-dh/2,pitch-dh))
    return min(1.2*lc*t*fu,2.4*db*t*fu)/G2,lc


def block_strength(Agv, Anv, Ant, fy, fu, gamma=G2):
    return min(0.6*fu*max(0,Anv)+fu*max(0,Ant),0.6*fy*max(0,Agv)+fu*max(0,Ant))/gamma


def net_plastic_modulus(h,t,n,p,dh):
    # Integração exata de |y|: contempla também o furo sobre o eixo neutro.
    integral=lambda y:0.5*y*abs(y)
    void=sum(integral((i-(n-1)/2)*p+dh/2)-integral((i-(n-1)/2)*p-dh/2) for i in range(n))
    return t*(h*h/4-void)


def plate_ltb(h,t,L,fy,elastic_modulus=E,Cb=1.84):
    """Resistência nominal AISC F11, procedimento do P901 II.A-17B/19B."""
    lam=L*h/t**2;lp=.08*elastic_modulus/fy;lr=1.9*elastic_modulus/fy
    Mp=fy*t*h*h/4;My=fy*t*h*h/6
    if lam<=lp: Mn=Mp
    elif lam<=lr: Mn=min(Mp,Cb*(1.52-.274*lam*fy/elastic_modulus)*My)
    else: Mn=min(Mp,1.9*elastic_modulus*Cb/lam*(t*h*h/6))
    return Mn,lam


def interaction(N,Nr,M,Mr,V,Vr,My=0,Myr=1):
    """AISC Manual 16 ed., 12-2/12-3. Expoente 2 no colchete inteiro."""
    p=abs(N)/Nr;b=abs(M)/Mr+abs(My)/Myr
    return (p/2+b if p<.2 else p+8*b/9)**2+(abs(V)/Vr)**2


def geometry(c:Connection):
    out=[]
    def issue(level,text,ref="Geometria e domínio do modelo"):out.append(Issue(level,text,ref))
    vals=[c.db,c.pitch,c.edge_v,c.edge_h,c.a,c.gap,c.tp,c.weld,c.fw,c.plate_top,c.beam_level,c.V,c.N,c.tool_radius,c.clearance,c.cope_top,c.cope_bottom,c.cope_length]
    if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in vals):
        issue("error","Todos os valores precisam ser números finitos.");return out,{}
    if c.kind not in ("column_flange","beam_web") or c.cope not in ("none","top","both"):
        issue("error","Configuração de ligação não reconhecida.");return out,{}
    if not isinstance(c.n,int) or not 2<=c.n<=12:
        issue("error","A V1 permite uma coluna vertical de 2 a 12 parafusos.");return out,{}
    if min(c.db,c.pitch,c.edge_v,c.edge_h,c.a,c.tp,c.weld,c.fw)<=0 or min(c.gap,c.clearance,c.tool_radius,c.plate_top)<0:
        issue("error","Dimensões positivas são obrigatórias; folgas e cotas de posicionamento não podem ser negativas.");return out,{}
    if not any(abs(c.db-v)<1e-8 for v in DIAMETERS.values()):
        issue("error","Diâmetro fora do catálogo em polegadas da V1.");return out,{}
    if c.bolt not in BOLTS or any(x not in STEELS for x in (c.beam_steel,c.support_steel,c.plate_steel)):
        issue("error","Material não reconhecido.");return out,{}
    for p in (c.beam,c.support):
        pv=[p.d,p.bf,p.tw,p.tf,p.clear,p.area,p.mass]
        if not all(isinstance(x,(int,float)) and math.isfinite(x) and x>0 for x in pv) or p.d<=2*p.tf or p.bf<=p.tw or p.clear>p.d-2*p.tf+1:
            issue("error",f"Geometria inconsistente do perfil {p.name}.");return out,{}
    if c.N<0:issue("pending","Compressão axial está fora do domínio validado da V1. Os cálculos de tração não serão aplicados a esse caso.")
    if c.cope!="none" and (min(c.cope_top,c.cope_length)<=0 or (c.cope=="both" and c.cope_bottom<=0)):
        issue("error","As dimensões dos recortes ativos devem ser positivas.")
    if c.coped_top+c.coped_bottom>=c.beam.d:
        issue("error","Os recortes eliminam a seção da viga.")
    if c.cope!="none":
        issue("pending","Recortes: geometria, bordas e seção líquida são avaliadas; estabilidade da região recortada e sua flexão ainda requerem verificação externa. Não há aprovação completa dessa variante.","AISC Manual Parte 9; P901, exemplo II.A-18")
    if (c.N>0 or c.a>89) and not c.restrained:
        issue("pending","Confirmar contenção eficaz contra rotação longitudinal da viga. A V1 calcula o momento de excentricidade transversal, mas a estabilidade do conjunto sem essa contenção ainda não está validada.","P901, II.A-17B e II.A-19B")
    if c.kind=="beam_web" and c.N>0:
        issue("pending","A flexão fora do plano da alma da viga de apoio sob a tração N ainda exige verificação específica. As verificações de corte local não a substituem.","NBR 8800, 6.5.1; domínio da V1")
    if c.kind=="column_flange" and c.N>0 and c.support.family in ("CS","CVS","VS","Soldado"):
        issue("pending","Para o pilar soldado, conferir a transmissão da força localizada pela solda mesa–alma da própria seção, cuja dimensão não consta do catálogo.","NBR 8800, 5.7.1")
    if not c.norm_minimum:
        issue("pending","Mínimo de 45 kN desativado: modo de comparação, sem conclusão de atendimento normativo.","NBR 8800, 6.1.5.2")
    for label,steel,t,plate in [("Chapa",c.plate_steel,c.tp,True),("Viga",c.beam_steel,max(c.beam.tf,c.beam.tw),c.beam.family in ('CS','CVS','VS','Soldado')),("Apoio",c.support_steel,max(c.support.tf,c.support.tw),c.support.family in ('CS','CVS','VS','Soldado'))]:
        s=STEELS[steel];limit=s.plate_max if plate else s.profile_max
        if (plate and not s.plate_allowed) or t>limit:
            issue("error",f"{label}: produto/espessura fora do intervalo cadastrado para {steel}.","NBR 8800, tabela A.2")
    pmin=max(2.7*c.db,c.dh+c.db)
    tmin=min(c.tp,c.beam.tw)
    pmax=min(24*tmin,300)
    if c.pitch<pmin:issue("error",f"Passo p = {c.pitch:g} mm inferior ao mínimo {pmin:.2f} mm.","NBR 8800, 6.3.9")
    if c.pitch>pmax:issue("error",f"Passo p excede {pmax:.2f} mm para elementos pintados ou não sujeitos à corrosão.","NBR 8800, 6.3.10(a)")
    if c.beam_edge<=c.dh/2:issue("error","O furo intercepta a extremidade da viga; aumentar a ou reduzir g.")
    emin={12.7:19,15.875:22,19.05:25,22.225:28,25.4:32,28.575:38,31.75:41}[c.db]
    for label,e in [("borda vertical da chapa",c.edge_v),("borda livre da chapa",c.edge_h),("extremidade da viga",c.beam_edge)]:
        if e<c.dh/2:issue("error",f"O furo intercepta a {label}.")
        elif e<emin:issue("pending",f"Distância à {label} = {e:.2f} mm abaixo da tabela 16 ({emin} mm). A exceção da tabela requer conferência específica de pressão de contato.","NBR 8800, 6.3.11 / tabela 16")
    for label,e,t in [("borda vertical da chapa",c.edge_v,c.tp),("borda livre da chapa",c.edge_h,c.tp),("extremidade da viga",c.beam_edge,c.beam.tw)]:
        if e>min(12*t,150):issue("error",f"Distância à {label} excede min(12t; 150 mm).","NBR 8800, 6.3.12")
    limit_t=c.db/2+(1.6 if c.n<=5 else -1.6)
    ductile=min(c.tp,c.beam.tw)<=limit_t and min(c.edge_h,c.beam_edge)>=2*c.db
    if not ductile:issue("pending","Fora da dispensa simplificada de ductilidade: conferir a resistência nominal do grupo sob momento puro e a espessura máxima da chapa. Não basta a resistência sob a carga aplicada.","Carini, Ligações Flexíveis p.32–34; AISC Parte 10")
    if c.bolt=="ASTM A307":issue("pending","O detalhamento de ductilidade da single plate com parafusos comuns A307 não está validado nesta versão.")
    k=(c.beam.d-c.beam.clear)/2
    if c.plate_top<max(k,c.coped_top)+c.weld or c.plate_top+c.hp>min(c.beam.d-k,c.beam.d-c.coped_bottom)-c.weld:
        issue("error","A chapa/solda invade a região de mesa, concordância ou recorte da viga apoiada. Ajustar altura ou posição da chapa.")
    for y in c.y_bolts:
        if min(y-max(k,c.coped_top),min(c.beam.d-k,c.beam.d-c.coped_bottom)-y)<c.tool_radius:
            issue("error","Há interferência do envelope de montagem de parafuso/porca com mesa, concordância ou recorte.");break
    if c.a<c.weld+c.tool_radius:issue("error","Envelope de montagem do parafuso invade a solda/face do apoio.")
    ts=c.support.tf if c.kind=="column_flange" else c.support.tw
    smaller=min(c.tp,ts)
    wmin=3 if smaller<=6.3 else 5 if smaller<=12.5 else 6 if smaller<=19 else 8
    if c.weld<wmin:issue("error",f"Filete inferior ao mínimo de {wmin} mm para a menor espessura da junta.","NBR 8800, 6.2.6.2.1 / tabela 11")
    wmax=c.tp if c.tp<6.3 else c.tp-1.5
    if c.weld>wmax+1e-8 and not c.reinforced_weld:issue("error",f"Filete superior a {wmax:.2f} mm na borda da chapa. Redimensionar ou especificar execução reforçada.","NBR 8800, 6.2.6.2.2")
    if c.hp<max(4*c.weld,40):issue("error","Comprimento de solda inferior ao mínimo.","NBR 8800, 6.2.6.2.3")
    # Perna mínima do procedimento AISC; fora da combinação material de referência não extrapolar.
    if STEELS[c.plate_steel].fy>345 or c.fw<485:
        issue("pending","Procedimento de solda que desenvolve a chapa ainda não validado para fy > 345 MPa ou eletrodo inferior a E70. Resistência direta calculada; ductilidade da junta pendente.","P901, II.A-17B / II.A-19B")
    elif c.weld+1e-8<.625*c.tp:
        issue("error",f"Procedimento single plate exige perna ≥ 5t/8 = {.625*c.tp:.2f} mm.","P901, II.A-17B, resistência da solda")
    if c.kind=="beam_web":
        ks=(c.support.d-c.support.clear)/2
        py=c.beam_level+c.plate_top
        if py<ks+c.weld or py+c.hp>c.support.d-ks-c.weld:
            issue("error","Chapa/solda interfere nas mesas ou concordâncias da viga de apoio.")
        projection=(c.support.bf-c.support.tw)/2
        # Nas faixas ocupadas pelas mesas do apoio, é necessário afastar a ponta
        # da viga ou retirar material. Folga de montagem explicitamente configurável.
        full_low=c.beam_level;full_high=full_low+c.beam.d
        for label,lo,hi,depth in [("superior",-c.clearance,c.support.tf+c.clearance,c.coped_top),("inferior",c.support.d-c.support.tf-c.clearance,c.support.d+c.clearance,c.coped_bottom)]:
            overlaps=full_high>lo and full_low<hi
            if overlaps and c.gap<projection+c.clearance:
                enough_length=c.cope!="none" and c.gap+c.cope_length>=projection+c.clearance
                enough_depth=(full_low+depth>=hi) if label=="superior" else (full_high-depth<=lo)
                if not (enough_length and enough_depth):issue("error",f"Interferência com a mesa {label} da viga de apoio. Afastar a ponta ou ajustar o recorte e a folga.")
    if c.plate_top+c.hp>c.beam.d:issue("error","A chapa ultrapassa a altura da viga apoiada.")
    if c.tp+c.beam.tw>5*c.db:issue("pending","Pega longa: redução da resistência do parafuso ainda não implementada.","NBR 8800, 6.3.7")
    if c.N>0 and abs(c.eccentric_n)>1e-6:
        issue("info",f"N é referido ao eixo da viga. Incluído |N·eN|, com eN = {c.eccentric_n:.2f} mm, no momento local.")
    g=dict(hp=c.hp,width=c.width,dh=c.dh,dh_net=c.dh_net,beam_edge=c.beam_edge,e=c.a,emin=emin,pmin=pmin,pmax=pmax,ductile=ductile,ts=ts)
    return out,g


def strength(c:Connection, V:float, N:float, case="Entrada"):
    rows=[]
    def add(id,name,S,R,unit,ref,eq,subst,variables):
        rows.append(Check(id,name,S,R,unit,ref,eq,subst,variables,case))
    b=STEELS[c.beam_steel];s=STEELS[c.support_steel];p=STEELS[c.plate_steel]
    V=abs(V);N=abs(N);h=c.hp;t=c.tp;dn=c.dh_net
    M=V*c.a+N*abs(c.eccentric_n)  # envoltória dos sinais da excentricidade axial
    F=elastic_bolts(c.n,c.pitch,V,N,M);Fmax=max(math.hypot(x,y) for x,y in F)
    add("bolts","Parafusos em corte simples",Fmax,bolt_shear(c.db,BOLTS[c.bolt],c.threads or c.bolt=="ASTM A307"),"N",f"{NBR}, 6.3.3.2","F_Rd = α·π·db²·fub / (4·γa2)",f"Fmax = {Fmax:.2f} N; α = {0.45 if c.threads or c.bolt=='ASTM A307' else 0.56}; db = {c.db:g}; fub = {BOLTS[c.bolt]:g}; γa2 = {G2}","Fmax: resultante do parafuso crítico; db: diâmetro; fub: ruptura do aço do parafuso; α: coeficiente do plano de corte.")
    for id,label,th,fu,edge in [("bearing_plate","Contato e rasgamento da chapa",t,p.fu,min(c.edge_h,c.edge_v)),("bearing_beam","Contato e rasgamento da alma",c.beam.tw,b.fu,min(c.beam_edge,c.pitch-c.dh/2,min(c.y_bolts)-c.coped_top,c.beam.d-c.coped_bottom-max(c.y_bolts)))]:
        R,lc=bearing(c.db,c.dh,edge,c.pitch,th,fu)
        add(id,label,Fmax,R,"N",f"{NBR}, 6.3.3.3(a)","F_Rd = min(1,2·lc·t·fu; 2,4·db·t·fu) / γa2",f"lc conservador = {lc:.3f} mm; t = {th:g}; fu = {fu:g}; Fmax = {Fmax:.2f} N","lc: menor distância livre possível a bordas ou furos, adotada para qualquer direção da força; t: espessura ligada; fu: ruptura do metal-base.")
    Ag=h*t;An=(h-c.n*dn)*t;Zg=t*h*h/4;Zn=net_plastic_modulus(h,t,c.n,c.pitch,dn)
    Vy=.6*p.fy*Ag/G1;Vu=.6*p.fu*An/G2;Ny=p.fy*Ag/G1;Nu=p.fu*An/G2
    Mnom,lam=plate_ltb(h,t,c.a,p.fy);My=Mnom/G1;Mu=p.fu*Zn/G2
    for id,label,dem,cap,unit,ref,eq,sub,vars in [
        ("plate_vy","Chapa — escoamento por corte",V,Vy,"N","6.5.5(a)","V_Rd = 0,60·fy·Ag / γa1",f"Ag = {h:.3f}×{t:.4f} = {Ag:.3f} mm²; fy = {p.fy:g}","Ag: área bruta; fy: escoamento; γa1 = 1,10."),
        ("plate_vu","Chapa — ruptura por corte",V,Vu,"N","6.5.5(b)","V_Rd = 0,60·fu·An / γa2",f"An = ({h:.3f} − {c.n}×{dn:.4f})×{t:.4f} = {An:.3f} mm²","An: área líquida; desconto do furo inclui acréscimo de 2 mm, salvo furação com broca; γa2 = 1,35."),
        ("plate_ny","Chapa — escoamento por tração",N,Ny,"N","6.5.3(a)","N_Rd = fy·Ag / γa1",f"{p.fy:g}×{Ag:.3f}/{G1}","N: força axial de tração; Ag: área bruta."),
        ("plate_nu","Chapa — ruptura por tração",N,Nu,"N","6.5.3(b)","N_Rd = fu·An / γa2",f"{p.fu:g}×{An:.3f}/{G2}","Área diretamente conectada da chapa; Ct = 1,0; não é uma emenda de barras."),
        ("plate_mu","Chapa — ruptura por flexão",M,Mu,"Nmm","6.5; complemento AISC Manual 9-8","M_Rd = fu·Zn / γa2",f"Zn = {Zn:.3f} mm³; fu = {p.fu:g}; M = |V|a + |N·eN| = {M:.3f} Nmm","Zn: módulo plástico líquido integrado descontando todos os furos; M: momento local, não momento de engaste."),
    ]: add(id,label,dem,cap,unit,f"{NBR}, {ref}",eq,sub,vars)
    add("plate_ltb","Chapa — flexão e estabilidade",M,My,"Nmm","P901 II.A-17B/19B, AISC F11; γa1 da NBR 8800","Mn = min(Mp; Cb·(1,52 − 0,274·λ·fy/E)·fy·W); M_Rd = Mn/γa1",f"λ = a·h/t² = {lam:.3f}; Cb = 1,84; Mp = {p.fy*Zg:.3f} Nmm; Mn = {Mnom:.3f} Nmm","E = 200 000 MPa; Lb = a; W = th²/6; Mp = fyth²/4. Usar Mp se λ ≤ 0,08E/fy; para λ > 1,9E/fy, Mn = min(Mp; 1,9ECbW/λ).")
    minor=0 if c.restrained else N*(t+c.beam.tw)/2
    minor_y=p.fy*h*t*t/4/G1;minor_u=p.fu*(h-c.n*dn)*t*t/4/G2
    for suffix,Nr,Mr,Vr,Myr,label in [("y",Ny,My,Vy,minor_y,"escoamento e estabilidade"),("u",Nu,Mu,Vu,minor_u,"ruptura")]:
        eta=interaction(N,Nr,M,Mr,V,Vr,minor,Myr)
        add("interaction_"+suffix,"Chapa — interação N V M / "+label,eta,1,"—","AISC Manual 16ª ed., 12-2/12-3; resistências NBR explícitas","η = [n/2 + m]² + v² (n < 0,2); η = [n + 8m/9]² + v² (n ≥ 0,2)",f"n = {N/Nr:.6f}; m = {M/Mr+minor/Myr:.6f}; v = {V/Vr:.6f}; η = {eta:.6f}","n = N/NRd; m = Mx/MxRd + My/MyRd; v = V/VRd; My = N(tp+tw)/2 sem contenção, ou zero com contenção confirmada. Complemento técnico, não equação da NBR.")
    # Caminhos L e U da chapa; uma coluna de parafusos, bordas simétricas.
    L=c.edge_v+(c.n-1)*c.pitch
    Av=L*t;Anv=(L-(c.n-.5)*dn)*t;At=(c.edge_h-.5*dn)*t
    Bv=block_strength(Av,Anv,At,p.fy,p.fu)
    Bn=block_strength(c.edge_h*t,(c.edge_h-.5*dn)*t,(L-(c.n-.5)*dn)*t,p.fy,p.fu)
    Bu=block_strength(2*c.edge_h*t,2*(c.edge_h-.5*dn)*t,((c.n-1)*c.pitch-(c.n-1)*dn)*t,p.fy,p.fu)
    blockeq="R_Rd = min(0,6·fu·Anv + fu·Ant; 0,6·fy·Agv + fu·Ant) / γa2"
    add("block_plate","Chapa — bloco L sob N e V",(V/Bv)**2+(N/Bn)**2,1,"—","NBR 8800, 6.5.6; AISC Manual 12-1",blockeq+"; η = (V/Rv)² + (N/Rn)²",f"Rv = {Bv:.3f} N; Rn = {Bn:.3f} N; Agv,V = {Av:.3f}; Anv,V = {Anv:.3f}; Ant,V = {At:.3f} mm²","Agv, Anv: áreas bruta/líquida ao corte; Ant: área líquida à tração; Cts = 1,0 no caminho L desta geometria.")
    add("block_plate_u","Chapa — bloco U sob tração",N,Bu,"N",f"{NBR}, 6.5.6",blockeq,f"Agv = {2*c.edge_h*t:.3f}; Anv = {2*(c.edge_h-.5*dn)*t:.3f}; Ant = {((c.n-1)*c.pitch-(c.n-1)*dn)*t:.3f} mm²","Caminho U entre a borda livre e os furos extremos; Cts = 1,0.")
    beam_h=c.beam.d-c.coped_top-c.coped_bottom
    Hb=min(c.beam.clear,beam_h);Ab=Hb*c.beam.tw;Anb=(Hb-c.n*dn)*c.beam.tw
    add("beam_v","Alma apoiada — corte local",V,.6*b.fy*Ab/G1,"N",f"{NBR}, 6.5.5(a)","V_Rd = 0,60·fy·hweb·tw/γa1",f"hweb = {Hb:.3f}; tw = {c.beam.tw:g}; fy = {b.fy:g}","hweb: altura livre da alma considerada localmente; verificação global da viga é externa ao app.")
    # Somente a faixa da alma conectada é usada na resistência axial (limite conservador).
    add("beam_n","Alma apoiada — tração na faixa conectada",N,min(b.fy*Ab/G1,b.fu*Anb/G2),"N",f"{NBR}, 6.5.3; 5.2.4","N_Rd = min(fy·Aweb/γa1; fu·Anweb/γa2)",f"Aweb = {Ab:.3f}; Anweb = {Anb:.3f} mm²; fy = {b.fy:g}; fu = {b.fu:g}","Adota apenas a alma, sem contribuição das mesas: limite conservador para introdução da tração.")
    Bu_b=block_strength(2*c.beam_edge*c.beam.tw,2*(c.beam_edge-.5*dn)*c.beam.tw,((c.n-1)*(c.pitch-dn))*c.beam.tw,b.fy,b.fu)
    add("block_beam_u","Alma apoiada — bloco U sob tração",N,Bu_b,"N",f"{NBR}, 6.5.6",blockeq,f"Agv = {2*c.beam_edge*c.beam.tw:.3f}; Anv = {2*(c.beam_edge-.5*dn)*c.beam.tw:.3f}; Ant = {(c.n-1)*(c.pitch-dn)*c.beam.tw:.3f} mm²","Caminho U na extremidade da alma apoiada; Cts = 1,0.")
    # Mecanismo de interação da alma do roteiro Carini / SCI, acrescido de N linear.
    ell=(c.n-1)*c.pitch
    Vbc=V*ell/beam_h;VbcR=.6*b.fy*ell*c.beam.tw/G1
    reduction=max(0,1-(2*Vbc/VbcR-1)**2) if Vbc>.5*VbcR else 1
    Mbc=c.beam.tw*ell**2/6*b.fy/G1*reduction
    Vab=.6*b.fy*c.beam_edge*c.beam.tw/G1
    webM=Mbc+Vab*ell
    add("beam_vm","Alma apoiada — interação local",M/webM+N/(b.fy*h*c.beam.tw/G1) if webM>0 else math.inf,1,"—","Carini, Ligações Flexíveis p.41; SCI/BCSA 2014; extensão conservadora linear para N","η = M/(M_BC,Rd + V_AB,Rd·ℓ) + N/Nweb,Rd",f"ℓ = {ell:.3f}; M_BC,Rd = {Mbc:.3f}; V_AB,Rd = {Vab:.3f}; M_Rd = {webM:.3f} Nmm","ℓ: altura entre furos extremos; BC: faixa vertical; AB: ligamento horizontal. M_BC é reduzido quando V_BC > 0,5V_BC,Rd. Interação linear adicional de N é opção conservadora de implementação.")
    # Dois filetes: análise elástica de linha, sem majoração direcional de resistência.
    q=math.hypot(N/(2*h)+3*M/h**2,V/(2*h))
    qr=.6*c.fw*(c.weld/math.sqrt(2))/G2
    add("weld","Soldas — metal de adição",q,qr,"N/mm",f"{NBR}, 6.2.5 / tabela 9","qmax = √[(N/2h + 3M/h²)² + (V/2h)²]; qRd = 0,6·fw·(w/√2)/γw2",f"qmax = {q:.5f}; qRd = {qr:.5f}; h = {h:.3f}; w = {c.weld:g}; fw = {c.fw:g}","Dois filetes verticais; γw2 = 1,35. Envoltória conservadora com o momento local completo também na solda; sem aumento direcional da resistência.")
    ts=c.support.tf if c.kind=="column_flange" else c.support.tw
    add("base_plate","Metal-base da chapa junto à solda",2*q,min(.6*p.fy*t/G1,.6*p.fu*t/G2),"N/mm",f"{NBR}, 6.5.5","qRd = min(0,6·fy·tp/γa1; 0,6·fu·tp/γa2)",f"qSd = 2×{q:.5f}; tp = {t:.4f}; fy = {p.fy:g}; fu = {p.fu:g}","Resultante por unidade de comprimento; critério de cisalhamento conservador para a resultante combinada.")
    add("support_shear","Apoio — corte e ruptura local",math.hypot(V,N),min(.6*s.fy*2*h*ts/G1,.6*s.fu*2*h*ts/G2),"N",f"{NBR}, 6.5.5; P901 II.A-17B/19B","R_Rd = min(0,6·fy·2h·ts/γa1; 0,6·fu·2h·ts/γa2)",f"h = {h:.3f}; ts = {ts:g}; fy = {s.fy:g}; fu = {s.fu:g}","ts: espessura efetivamente soldada, mesa do pilar ou alma da viga. Esta verificação não cobre flexão fora do plano da alma do apoio.")
    # Critério conservador de hierarquia chapa/apoio do roteiro Carini.
    punch_limit=ts*s.fu/(p.fy*G2)
    add("support_punch","Apoio — hierarquia contra punção",t,punch_limit,"mm","Carini, Ligações Flexíveis p.43, critério conservador SCI/BCSA","tp ≤ ts·fu,s / (fy,p·γa2)",f"{t:.4f} ≤ {ts:g}×{s.fu:g}/({p.fy:g}×{G2}) = {punch_limit:.4f}","Limita a espessura da chapa para que o apoio não governe por punção antes de seu escoamento.")
    if c.kind=="column_flange":
        if c.tp+2*c.weld >= .15*c.support.bf:
            add("support_flange","Pilar — flexão local da mesa por N",N,.5*6.25*c.support.tf**2*s.fy/G1,"N",f"{NBR}, 5.7.2.2 e 5.7.2.3","R_Rd = 0,5·6,25·tf²·fy/γa1",f"tf = {c.support.tf:g} mm; fy = {s.fy:g} MPa; redução 0,5 para proximidade à extremidade","Verificação quando a largura carregada tp+2w ≥ 0,15bf. Adotada a redução de extremidade por não se informar a distância ao topo do pilar.")
        # Adotado caso de extremidade, conservador, sem solicitar distância adicional.
        Ry=1.10*(2.5*c.support.tf+h)*s.fy*c.support.tw/G1
        add("support_web_y","Pilar — escoamento local da alma por N",N,Ry,"N",f"{NBR}, 5.7.3.2(b)","R_Rd = 1,10·(2,5k + ln)·fy·tw/γa1",f"k = tf = {c.support.tf:g} mm; ln = {h:.3f} mm; tw = {c.support.tw:g}","Caso próximo à extremidade, conservador; k adota apenas tf, sem ganho do raio ou filete. Aplicável à chapa na mesa alinhada à alma.")
    return rows


def evaluate(c:Connection):
    issues,g=geometry(c);r=Result(issues=issues,geometry=g)
    if any(i.severity=="error" for i in issues) or c.N<0:return r
    b=STEELS[c.beam_steel]
    if c.beam.clear/c.beam.tw>1.1*math.sqrt(5*E/b.fy):
        r.issues.append(Issue("pending","Alma da viga apoiada esbelta ao corte: resistência com instabilidade ainda não implementada.","NBR 8800, 5.4.3"))
    try:
        r.actual=strength(c,c.V,c.N)
        R=math.hypot(c.V,c.N)
        factor=max(1,45000/R) if c.norm_minimum and R>0 else 1
        r.minimum_factor=factor
        r.checks=strength(c,c.V*factor,c.N*factor,"Mínimo normativo de 45 kN" if factor>1 else "Entrada")
        if R==0:r.issues.append(Issue("pending","Esforços nulos: a direção do mínimo normativo não está definida. Informe o caso de cálculo."))
        if factor>1:r.issues.append(Issue("info",f"Entrada preservada. Verificação adicional com resultante de 45 kN na mesma direção: V = {c.V*factor/1000:.3f} kN; N = {c.N*factor/1000:.3f} kN.","NBR 8800, 6.1.5.2"))
    except (ZeroDivisionError,ValueError,OverflowError) as exc:
        r.issues.append(Issue("error","Geometria produz áreas ou resistências inválidas. Revise furos, recortes e dimensões."))
        r.actual=[];r.checks=[]
    return r
