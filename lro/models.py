"""Valores canônicos: N, mm, MPa. Nenhum fator de carga neste módulo."""
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import math

KGF = 9.80665
VERSION = "0.1.0"


@dataclass(frozen=True)
class Profile:
    name: str
    family: str
    mass: float
    d: float
    bf: float
    tw: float
    tf: float
    clear: float
    area: float
    source: str = "Seção informada pelo usuário"


def profiles():
    path = Path(__file__).resolve().parent.parent / "data" / "profiles.json"
    rows=json.loads(path.read_text(encoding="utf-8"))
    result={p["name"]: Profile(**p) for p in rows}
    if len(result)!=len(rows):raise ValueError("O catálogo contém designações ambíguas; identificar as variantes antes de utilizar.")
    return result


@dataclass(frozen=True)
class Steel:
    name: str
    fy: float
    fu: float
    plate_max: float = 200.0
    profile_max: float = 200.0
    plate_allowed: bool = True


# NBR 8800:2024, tabela A.2. Valores mínimos; limites de produto explícitos.
STEELS = {
    s.name: s for s in [
        Steel("ASTM A36",250,400),
        Steel("ASTM A572 Gr.42",290,415,150),
        Steel("ASTM A572 Gr.50",345,450,100),
        Steel("ASTM A572 Gr.55",380,485,50),
        Steel("ASTM A572 Gr.60",415,520,31.5,50),
        Steel("ASTM A572 Gr.65",450,550,31.5,50),
        Steel("ASTM A992",345,450,0,200,False),
        Steel("ASTM A913 Gr.50",345,450,0,50,False),
        Steel("ASTM A913 Gr.60",415,520,0,50,False),
        Steel("ASTM A913 Gr.65",450,550,0,50,False),
    ]
}

BOLTS = {"ASTM F3125 A325":830.0, "ASTM F3125 A490":1040.0, "ASTM A307":415.0}
DIAMETERS = {"1/2\"":12.7,"5/8\"":15.875,"3/4\"":19.05,"7/8\"":22.225,"1\"":25.4,"1 1/8\"":28.575,"1 1/4\"":31.75}
THICKNESSES = {"1/4\"":6.35,"5/16\"":7.9375,"3/8\"":9.525,"1/2\"":12.7,"5/8\"":15.875,"3/4\"":19.05}


@dataclass(frozen=True)
class Connection:
    beam: Profile
    support: Profile
    kind: str = "column_flange"
    beam_steel: str = "ASTM A572 Gr.50"
    support_steel: str = "ASTM A572 Gr.50"
    plate_steel: str = "ASTM A36"
    bolt: str = "ASTM F3125 A325"
    db: float = 19.05
    threads: bool = True
    n: int = 3
    pitch: float = 70.0
    edge_v: float = 40.0
    edge_h: float = 40.0
    a: float = 75.0
    gap: float = 10.0
    tp: float = 7.9375
    weld: float = 5.0
    fw: float = 485.0
    reinforced_weld: bool = False
    plate_top: float = 66.5
    beam_level: float = 0.0
    cope: str = "none"
    cope_top: float = 25.0
    cope_bottom: float = 25.0
    cope_length: float = 80.0
    clearance: float = 10.0
    tool_radius: float = 18.0
    drilled: bool = False
    V: float = 11000.0
    N: float = 2000.0
    restrained: bool = False
    norm_minimum: bool = True
    notes: str = ""
    project: str = "Ligação single plate"

    @property
    def hp(self): return 2*self.edge_v+(self.n-1)*self.pitch
    @property
    def width(self): return self.a+self.edge_h
    @property
    def beam_edge(self): return self.a-self.gap
    @property
    def dh(self): return self.db+(1.5875 if self.db < 25.4 else 3.175)
    @property
    def dh_net(self): return self.dh+(0 if self.drilled else 2.0)
    @property
    def y_bolts(self): return [self.plate_top+self.edge_v+i*self.pitch for i in range(self.n)]
    @property
    def yc(self): return self.plate_top+self.hp/2
    @property
    def eccentric_n(self): return self.beam.d/2-self.yc
    @property
    def coped_top(self): return self.cope_top if self.cope in ("top","both") else 0.0
    @property
    def coped_bottom(self): return self.cope_bottom if self.cope=="both" else 0.0

    def to_dict(self): return {"schema_version":1,"app_version":VERSION,"connection":asdict(self)}

    @staticmethod
    def from_dict(data):
        if not isinstance(data,dict):raise ValueError("O projeto deve ser um objeto JSON.")
        if data.get("schema_version") != 1: raise ValueError("Versão de arquivo de projeto não reconhecida.")
        if not isinstance(data.get("connection"),dict):raise ValueError("O arquivo não contém os dados da ligação.")
        d=dict(data["connection"])
        d["beam"]=Profile(**d["beam"]);d["support"]=Profile(**d["support"])
        return Connection(**d)


@dataclass
class Check:
    id: str
    name: str
    demand: float
    resistance: float
    unit: str
    reference: str
    equation: str
    substitution: str
    variables: str
    case: str = "Entrada"

    @property
    def ratio(self):
        if self.resistance <= 0: return math.inf
        return abs(self.demand)/self.resistance

    @property
    def passed(self): return math.isfinite(self.ratio) and self.ratio <= 1+1e-10


@dataclass
class Issue:
    severity: str
    text: str
    reference: str = "Geometria e domínio do modelo"


@dataclass
class Result:
    checks: list[Check] = field(default_factory=list)
    actual: list[Check] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    geometry: dict = field(default_factory=dict)
    minimum_factor: float = 1.0

    @property
    def status(self):
        if any(x.severity=="error" for x in self.issues):return "GEOMETRIA INVÁLIDA"
        if any(not c.passed for c in self.checks):return "NÃO ATENDE"
        if any(x.severity=="pending" for x in self.issues):return "VERIFICAÇÃO INCOMPLETA"
        return "ATENDE AO ESCOPO VERIFICADO"

    @property
    def governing(self): return max(self.checks,key=lambda x:x.ratio) if self.checks else None
