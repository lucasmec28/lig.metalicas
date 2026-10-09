"""Conferências pontuais de exemplos publicados; não representam validação integral."""
import math
from .engine import elastic_bolts,interaction,plate_ltb,block_strength


def benchmarks():
    values=[]
    def add(name,calc,reference,unit,tol,source):
        values.append(dict(verificação=name,calculado=calc,referência=reference,unidade=unit,erro=abs(calc-reference),tolerância=tol,atende=abs(calc-reference)<=tol,fonte=source))
    f=elastic_bolts(2,75,45000,0,45000*37.5)
    add('Carini · força no parafuso (e = a/2)',max(math.hypot(x,y) for x,y in f)/1000,31.82,'kN',.01,'Anotações de aula, PDF p.4; geometria original, V puro')
    add('Carini · ruptura ao corte da chapa',.6*400*(155-2*22.55)*6.3/1.35/1000,123.0,'kN',.15,'Anotações de aula, PDF p.5; espessura e furação originais')
    add('AISC II.A-17B · interação de escoamento',interaction(60,327,188,1180,75,218),.181,'—',.002,'P901-23W, IIA-187 / PDF p.727')
    add('AISC II.A-17B · interação de ruptura',interaction(60,232,188,840,75,139),.500,'—',.002,'P901-23W, IIA-188 / PDF p.728')
    add('AISC II.A-19B · interação de ruptura',interaction(60,332,731,1260,75,199),.592,'—',.003,'P901-23W, IIA-223 / PDF p.763')
    # Unidades kip/in/ksi para manter os dados originais sem adaptação brasileira.
    mn,_=plate_ltb(15,.75,9.75,50,elastic_modulus=29000,Cb=1.84)
    add('AISC II.A-19B · momento nominal da chapa',mn,2110,'kip·in',2,'P901-23W, IIA-219/220 / PDF p.759–760')
    add('AISC II.A-19B · bloco U da chapa',block_strength(7.5,4.83,5.44,50,65,gamma=1),542,'kip',1,'P901-23W, IIA-226 / PDF p.766; áreas arredondadas do exemplo')
    return values
