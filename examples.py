from dataclasses import replace
from .models import Connection, profiles


def presets():
    ps=profiles()
    beam=ps['W 360 x 39,0'];main=ps['W 410 x 38,8']
    common=Connection(beam=beam,support=main,kind='beam_web',a=120,gap=80,plate_top=(beam.d-220)/2)
    carini=Connection(beam=ps['W 310 x 21,0'],support=ps['W 150 x 22,5 (H)'],n=2,pitch=75,edge_v=40,edge_h=40,a=75,gap=10,tp=7.9375,weld=5,plate_top=35,V=45000,N=0,project='Carini adaptado à V1',notes='Referência: Anotações de aula, p.4–7. Chapa alterada de 6,3 mm para 5/16\" e procedimento geral e=a. Comparações dos componentes originais em Validação.')
    carini=replace(carini,gap=15,notes=carini.notes+' Folga alterada de 10 para 15 mm para respeitar a distância máxima à borda da alma de 5,1 mm.')
    return {
        'Seu caso · W360×39 → W410×38,8':common,
        'Carini · W310×21 → mesa W150×22,5':carini,
        'Viga → mesa de pilar W · 11 kN + 2 kN':replace(common,beam=main,support=ps['W 310 x 97,0 (H)'] if 'W 310 x 97,0 (H)' in ps else ps['W 150 x 22,5 (H)'],kind='column_flange',a=75,gap=10,plate_top=(main.d-220)/2),
    }
