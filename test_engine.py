from dataclasses import replace
import math
import json
import pytest
from lro.models import Connection,KGF
from lro.engine import evaluate,elastic_bolts,geometry,plate_ltb,interaction
from lro.examples import presets
from lro.benchmarks import benchmarks


@pytest.fixture
def carini():return list(presets().values())[1]


@pytest.mark.parametrize('row',benchmarks(),ids=lambda x:x['verificação'])
def test_published_component_benchmarks(row):
    assert row['atende'],row


@pytest.mark.parametrize('V,N,M',[(10000,2000,1400000),(-10000,2000,-1400000),(0,80000,0),(10000,0,0)])
def test_bolt_group_equilibrium(V,N,M):
    forces=elastic_bolts(5,70,V,N,M)
    assert sum(x for x,y in forces)==pytest.approx(N)
    assert sum(y for x,y in forces)==pytest.approx(V)
    recovered=sum(-((i-2)*70)*fx for i,(fx,fy) in enumerate(forces))
    assert recovered==pytest.approx(M)


def test_no_extra_factoring_and_minimum_case(carini):
    c=replace(carini,V=11000,N=2000,restrained=True)
    r=evaluate(c)
    assert (c.V,c.N)==(11000,2000)
    assert math.hypot(c.V*r.minimum_factor,c.N*r.minimum_factor)==pytest.approx(45000)
    assert r.actual[0].case=='Entrada'
    assert r.checks[0].case=='Mínimo normativo de 45 kN'
    assert r.checks[0].demand/r.actual[0].demand==pytest.approx(r.minimum_factor)


def test_catalog_and_units_roundtrip(carini):
    from lro.models import profiles
    catalog=profiles()
    assert len(catalog)==560
    assert len([k for k in catalog if k.startswith('VS 300 x 28')])==2
    restored=Connection.from_dict(json.loads(json.dumps(carini.to_dict())))
    assert restored==carini
    assert 11000/KGF==pytest.approx(1121.687834,abs=1e-6)
    assert evaluate(restored).checks==evaluate(carini).checks


def test_at_limit_no_rounding():
    from lro.models import Check
    c=Check('x','x',1.00001,1,'—','','','', '')
    assert not c.passed


@pytest.mark.parametrize('field,value',[('n',1),('pitch',0),('tp',0),('V',float('nan')),('N',float('inf')),('gap',100),('plate_top',-10),('db',18)])
def test_invalid_input_blocks_calculation(carini,field,value):
    r=evaluate(replace(carini,**{field:value}))
    assert r.status=='GEOMETRIA INVÁLIDA'
    assert not r.checks


def test_user_case_cannot_be_approved_with_unchecked_support():
    c=replace(next(iter(presets().values())),restrained=True)
    r=evaluate(c)
    assert r.status=='VERIFICAÇÃO INCOMPLETA'
    assert any('fora do plano' in i.text for i in r.issues)


def test_compression_never_reinterpreted_as_tension(carini):
    r=evaluate(replace(carini,N=-2000))
    assert r.status=='VERIFICAÇÃO INCOMPLETA'
    assert not r.checks


def test_no_cope_detects_flange_interference():
    c=replace(next(iter(presets().values())),gap=10,a=75)
    assert any(i.severity=='error' and 'mesa superior' in i.text for i in evaluate(c).issues)


def test_cope_resolves_geometry_but_does_not_approve_structure():
    c=replace(next(iter(presets().values())),gap=10,a=75,cope='top',cope_length=80,cope_top=25,N=0)
    r=evaluate(c)
    assert not any(i.severity=='error' for i in r.issues)
    assert r.status=='VERIFICAÇÃO INCOMPLETA'
    assert r.geometry['e']==75


def test_spacing_exact_boundary(carini):
    minimum=2.7*carini.db
    low=evaluate(replace(carini,pitch=minimum-.0001))
    exact=evaluate(replace(carini,pitch=minimum))
    assert any('Passo p =' in i.text for i in low.issues)
    assert not any('Passo p =' in i.text for i in exact.issues)


def test_35mm_is_not_automatically_a_valid_method(carini):
    r=evaluate(replace(carini,edge_h=35))
    assert any(i.severity=='pending' and 'ductilidade' in i.text for i in r.issues)
    assert not any('tabela 16' in i.text for i in r.issues)


def test_norm_hole_and_bolt_update(carini):
    from lro.engine import bolt_shear
    assert carini.dh==pytest.approx(20.6375)
    assert carini.dh_net==pytest.approx(22.6375)
    assert replace(carini,drilled=True).dh_net==pytest.approx(20.6375)
    assert bolt_shear(19.05,830)==pytest.approx(78856.88545029,rel=.0001)


def test_force_scaling_and_sign(carini):
    small=evaluate(carini);large=evaluate(replace(carini,V=90000));negative=evaluate(replace(carini,V=-45000))
    assert large.checks[0].demand==pytest.approx(2*small.checks[0].demand)
    assert [x.ratio for x in small.checks]==pytest.approx([x.ratio for x in negative.checks])


def test_weld_and_actual_support_thickness():
    c=next(iter(presets().values()));r=evaluate(c)
    assert r.geometry['ts']==c.support.tw
    assert evaluate(replace(c,kind='column_flange')).geometry['ts']==c.support.tf
    assert any('Filete inferior' in i.text for i in evaluate(replace(c,weld=3)).issues)


def test_zero_load_is_not_approved(carini):
    assert evaluate(replace(carini,V=0,N=0)).status=='VERIFICAÇÃO INCOMPLETA'


def test_minimum_deactivation_is_explicit(carini):
    r=evaluate(replace(carini,norm_minimum=False))
    assert r.status=='VERIFICAÇÃO INCOMPLETA'


def test_carini_adapted_is_in_scope(carini):
    r=evaluate(carini)
    assert r.status=='ATENDE AO ESCOPO VERIFICADO'
    assert len(r.checks)>=20


def test_material_product_restriction(carini):
    assert evaluate(replace(carini,plate_steel='ASTM A992')).status=='GEOMETRIA INVÁLIDA'


def test_welded_beam_cannot_use_rolled_only_steel(carini):
    welded=replace(carini.beam,family='Soldado')
    assert evaluate(replace(carini,beam=welded,beam_steel='ASTM A992')).status=='GEOMETRIA INVÁLIDA'


def test_failed_report_never_claims_all_checks_pass(carini):
    from io import BytesIO
    from docx import Document
    from lro.report import create_report
    overloaded=replace(carini,V=450000)
    result=evaluate(overloaded)
    assert result.status=='NÃO ATENDE'
    document=Document(BytesIO(create_report(overloaded,result)))
    text='\n'.join(p.text for p in document.paragraphs)
    assert 'A ligação não atende' in text
    assert 'As verificações locais incluídas nesta versão atendem' not in text


def test_higher_steel_does_not_silently_extend_weld_method(carini):
    r=evaluate(replace(carini,plate_steel='ASTM A572 Gr.65'))
    assert any(i.severity=='pending' and 'fy > 345' in i.text for i in r.issues)


def test_ltb_all_branches_are_positive_and_capped():
    fy=250;Mp=fy*8*200**2/4
    values=[plate_ltb(200,8,L,fy)[0] for L in [1,30,2000]]
    assert all(0<x<=Mp for x in values)
    assert values==sorted(values,reverse=True)
