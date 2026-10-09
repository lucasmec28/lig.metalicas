"""Desenho técnico a partir do mesmo objeto Connection usado nos cálculos."""
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon

BLUE='#225d86';INK='#243749';LIGHT='#e7eef4';ORANGE='#c9792f'


def connection_figure(c):
    fig,(ax,ap)=plt.subplots(1,2,figsize=(11.5,5.6),gridspec_kw={'width_ratios':[1.6,1]},layout='constrained')
    fig.patch.set_facecolor('white')
    def rect(a,x,y,w,h,color,edge=INK,alpha=1,lw=1.2):
        a.add_patch(Rectangle((x,y),w,h,facecolor=color,edgecolor=edge,lw=lw,alpha=alpha))
    def dim(a,p1,p2,label,offset=(0,0),rotation=0):
        a.annotate('',xy=p1,xytext=p2,arrowprops={'arrowstyle':'<->','color':INK,'lw':.8,'shrinkA':0,'shrinkB':0})
        mid=((p1[0]+p2[0])/2+offset[0],(p1[1]+p2[1])/2+offset[1])
        a.text(*mid,label,ha='center',va='center',fontsize=9,rotation=rotation,color=INK,bbox={'facecolor':'white','edgecolor':'none','pad':1.4})
    lev=c.beam_level if c.kind=='beam_web' else 0
    d=c.beam.d;end=max(c.width+120,c.gap+180)
    # Apoio em corte, face de solda x=0.
    if c.kind=='beam_web':
        s=c.support;q=(s.bf-s.tw)/2
        rect(ax,-s.tw,0,s.tw,s.d,'#d8dfe5')
        rect(ax,-s.tw-q,0,s.bf,s.tf,'#d8dfe5')
        rect(ax,-s.tw-q,s.d-s.tf,s.bf,s.tf,'#d8dfe5')
        left=-s.tw-q-20
    else:
        rect(ax,-c.support.tf,-25,c.support.tf,max(d+50,c.hp+70),'#d8dfe5')
        left=-c.support.tf-30
    # Seção longitudinal da viga; recortes removem material de verdade.
    g=c.gap;ct=c.coped_top;cb=c.coped_bottom;lc=c.cope_length
    coords=[(g,lev+ct),(g+lc,lev+ct),(g+lc,lev),(end,lev),(end,lev+d),(g+lc,lev+d),(g+lc,lev+d-cb),(g,lev+d-cb)]
    if c.cope=='none':coords=[(g,lev),(end,lev),(end,lev+d),(g,lev+d)]
    elif c.cope=='top':coords=[(g,lev+ct),(g+lc,lev+ct),(g+lc,lev),(end,lev),(end,lev+d),(g,lev+d)]
    ax.add_patch(Polygon(coords,closed=True,fc=LIGHT,ec=BLUE,lw=1.4))
    ax.plot([g+lc if ct else g,end],[lev+c.beam.tf]*2,color=BLUE,lw=.8)
    ax.plot([g+lc if cb else g,end],[lev+d-c.beam.tf]*2,color=BLUE,lw=.8)
    py=lev+c.plate_top
    rect(ax,0,py,c.width,c.hp,'#f8ddbb',ORANGE,alpha=.8)
    ax.plot([0,0],[py,py+c.hp],color=ORANGE,lw=4)
    for y in c.y_bolts:
        yy=lev+y
        ax.add_patch(Circle((c.a,yy),c.dh/2,fc='white',ec=BLUE,lw=1.2))
        ax.plot([c.a-c.dh*.3,c.a+c.dh*.3],[yy,yy],color=BLUE,lw=.7)
        ax.plot([c.a,c.a],[yy-c.dh*.3,yy+c.dh*.3],color=BLUE,lw=.7)
    base=max(lev+d,c.support.d if c.kind=='beam_web' else lev+d)
    dim(ax,(0,base+32),(c.a,base+32),f'a = {c.a:g}',(0,-1))
    dim(ax,(c.a,base+32),(c.width,base+32),f'eₕ = {c.edge_h:g}',(12,17))
    dim(ax,(c.width+22,py),(c.width+22,py+c.hp),f'hₚ = {c.hp:g}',(0,0),90)
    if c.n>1:dim(ax,(c.a-25,lev+c.y_bolts[0]),(c.a-25,lev+c.y_bolts[1]),f'p = {c.pitch:g}',(0,0),90)
    dim(ax,(0,lev-24),(g,lev-24),f'g = {g:g}',(0,-1))
    ax.text(end-12,lev+25,c.beam.name.replace(' x ','×'),ha='right',fontsize=10,color=BLUE,weight='bold')
    ax.text(left,base+65,c.support.name.replace(' x ','×'),fontsize=9,color=INK)
    ax.text(end-10,base+65,f'{c.n} parafusos · Ø {c.db:g} mm',fontsize=9,color=BLUE,ha='right')
    if c.cope!='none':ax.text(g+lc+5,lev-5,f'recorte {lc:g} × {ct:g}',fontsize=8,color=ORANGE)
    ax.set_xlim(left-10,end+20);ax.set_ylim(base+85,min(-48,lev-48));ax.set_aspect('equal')
    ax.set_title('VISTA LATERAL',loc='left',fontsize=11,weight='bold',color=INK,pad=12)
    ax.axis('off')
    # Planta local: chapa centrada no alinhamento da alma do pilar;
    # alma da viga encosta em uma face da chapa.
    half=max(c.beam.bf*.62,55);bcy=-(c.tp+c.beam.tw)/2
    ts=c.support.tf if c.kind=='column_flange' else c.support.tw
    rect(ap,-ts,-half,ts,2*half,'#d8dfe5')
    if c.kind=='column_flange':
        rect(ap,-65,-c.support.tw/2,65-ts,c.support.tw,'#d8dfe5')
    rect(ap,g,bcy-c.beam.bf/2,end-g,c.beam.bf,LIGHT,BLUE,alpha=.75)
    ap.plot([g,end],[bcy-c.beam.tw/2]*2,color=BLUE,ls='--',lw=1)
    ap.plot([g,end],[bcy+c.beam.tw/2]*2,color=BLUE,ls='--',lw=1)
    rect(ap,0,-c.tp/2,c.width,c.tp,'#f8ddbb',ORANGE)
    ap.add_patch(Polygon([(0,-c.tp/2),(c.weld,-c.tp/2),(0,-c.tp/2-c.weld)],fc=ORANGE,ec=ORANGE))
    ap.add_patch(Polygon([(0,c.tp/2),(c.weld,c.tp/2),(0,c.tp/2+c.weld)],fc=ORANGE,ec=ORANGE))
    ap.plot([c.a,c.a],[-c.tp/2-c.beam.tw-8,c.tp/2+8],color=INK,lw=3)
    ap.plot([c.a-9,c.a+9],[-c.tp/2-c.beam.tw-8]*2,color=INK,lw=3)
    ap.plot([c.a-9,c.a+9],[c.tp/2+8]*2,color=INK,lw=3)
    ap.annotate(f'tₚ = {c.tp:.2f} mm',xy=(c.width-15,0),xytext=(end-5,half+28),fontsize=9,color=ORANGE,ha='right',arrowprops={'arrowstyle':'-','color':ORANGE})
    ap.annotate(f'tw = {c.beam.tw:g} mm',xy=(end-35,bcy),xytext=(end-4,-half-25),fontsize=9,color=BLUE,ha='right',arrowprops={'arrowstyle':'-','color':BLUE})
    ap.annotate(f'2 filetes · w = {c.weld:g} mm',xy=(0,c.tp/2),xytext=(-50,half+25),fontsize=9,color=ORANGE,arrowprops={'arrowstyle':'-','color':ORANGE})
    ap.text(-50,-half-30,'Face do apoio',fontsize=9,color=INK)
    ap.set_xlim(-70,end+10);ap.set_ylim(half+55,-half-50);ap.set_aspect('equal');ap.axis('off')
    ap.set_title('PLANTA LOCAL',loc='left',fontsize=11,weight='bold',color=INK,pad=12)
    fig.text(.99,.012,'Cotas em mm · vistas proporcionais · conferir os avisos de geometria',ha='right',fontsize=8,color='#6b7c8c')
    return fig


def image_bytes(c,fmt='png'):
    fig=connection_figure(c);buf=BytesIO()
    fig.savefig(buf,format=fmt,dpi=190,facecolor='white',bbox_inches='tight')
    plt.close(fig)
    return buf.getvalue()
