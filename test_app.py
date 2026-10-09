from pathlib import Path
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'app.py'


def test_ui_load_change_and_export():
    at=AppTest.from_file(str(APP),default_timeout=30).run()
    assert not at.exception
    assert at.warning[0].value=='VERIFICAÇÃO INCOMPLETA'
    name=at.selectbox(key='example').options[1]
    at.selectbox(key='example').set_value(name)
    next(x for x in at.button if x.label=='Usar este exemplo').click().run()
    assert not at.exception
    assert any('ATENDE AO ESCOPO' in x.value for x in at.success)
    next(x for x in at.button if x.label=='Gerar memória Word').click().run()
    assert not at.exception
    initial_report=at.session_state['report']
    assert initial_report[2][:2]==b'PK'
    assert len(initial_report[2])>15000
    at.number_input(key='pitch').set_value(20.).run()
    assert not at.exception
    assert any('GEOMETRIA INVÁLIDA' in x.value for x in at.error)
    assert next(x for x in at.button if x.label=='Gerar memória Word').disabled
    # Relatório antigo não pode continuar disponível após alteração das entradas.
    assert not any(getattr(x,'label','')=='Baixar memória .docx' for x in at.get('download_button'))


def test_profile_change_applies_visible_material_default():
    at=AppTest.from_file(str(APP),default_timeout=30).run()
    at.selectbox(key='support_name').set_value('CS 600 x 281').run()
    assert not at.exception
    assert at.selectbox(key='support_steel').value=='ASTM A36'
    at.selectbox(key='kind').set_value('column_flange').run()
    assert not at.exception


def test_saved_project_import_callback():
    import json
    from lro.examples import presets
    sample=list(presets().values())[1]
    at=AppTest.from_file(str(APP),default_timeout=30).run()
    at.get('file_uploader')[0].upload('projeto.json',json.dumps(sample.to_dict()).encode(),'application/json').run()
    next(x for x in at.button if x.label=='Abrir arquivo').click().run()
    assert not at.exception
    assert at.text_input(key='project').value==sample.project
    assert at.number_input(key='V_kgf').value==sample.V/9.80665
