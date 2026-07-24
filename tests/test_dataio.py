import sys, os, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
import pandas as pd
from pathlib import Path
from wellguard.dataio.gpn_archive import load_archive

def test_gpn_archive_requires_metadata():
    import tempfile
    p=Path(tempfile.mkdtemp())/'x.csv'; pd.DataFrame({'x':[1]}).to_csv(p,index=False)
    try: load_archive(p, {'x':'freq_hz'}, {}, pressure_unit='bar')
    except ValueError as e: assert 'metadata' in str(e)
    else: assert False

def test_gpn_archive_explicit_units():
    import tempfile
    p=Path(tempfile.mkdtemp())/'x.csv'
    from wellguard.generator import generate
    df=generate('normal',seed=0)
    df.to_csv(p,index=False)
    md={'asset_id_hash':'a','well_id_hash':'w','timezone':'UTC','sampling_interval_s':60,'unit_system':'SI'}
    out, meta=load_archive(p, {}, md, pressure_unit='bar')
    assert meta['qc']['schema_ok'] is True
