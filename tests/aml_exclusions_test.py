#!/usr/bin/env python3
"""Exercise actual Editor binding changes without touching repository sources."""
from pathlib import Path
import re, subprocess, sys, tempfile, unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from aml_keymap import aml_header, bindings, layer_body, mouse_positions, keymap_source
ROOT = Path(__file__).resolve().parents[1]

class AMLGeneration(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'config/LiNEA40.keymap').read_text()
        self.body = layer_body(self.source, 'layer_1')
        self.items = bindings(self.body)
    def changed(self, items):
        body = re.sub(r'(?<!sensor-)\bbindings\s*=\s*<.*?>;', 'bindings = <'+' '.join(items)+'>;', self.body, count=1, flags=re.DOTALL)
        return self.source.replace(self.body,body,1)
    def positions(self, source):
        return mouse_positions(source, key_count=41)
    def test_current(self):
        self.assertEqual(self.positions(self.source), [i for i,x in enumerate(self.items) if x.split()[0] not in {'&trans','&none'}])
    def test_add_remove_move(self):
        active = self.positions(self.source)
        empty = next(i for i in range(41) if i not in active)
        self.items[empty],self.items[active[0]]=self.items[active[0]],'&trans'
        self.assertEqual(self.positions(self.changed(self.items)), sorted((set(active)-{active[0]})|{empty}))
    def test_empty_layer_retains_cancellation(self):
        source=self.changed(['&trans']*41)
        self.assertEqual(self.positions(source),[])
        self.assertIn('AML_EXCLUDED_POSITIONS 65535',aml_header(source,key_count=41))
    def test_comments_and_multiline(self):
        self.assertEqual(self.positions(self.source.replace('&mkp MB1','&mkp\nMB1 /* &kp F1 */')),self.positions(self.source))
    def test_incomplete_slots_rejected(self):
        with self.assertRaisesRegex(AssertionError,'41 editable slots'):
            self.positions(self.changed(self.items[:-1]))
    def test_wrapper_and_incremental_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp); source=tmp/'editable.keymap';wrapper=tmp/'wrapper.keymap';output=tmp/'generated/aml.h'
            source.write_text(self.source);wrapper.write_text('#include "editable.keymap"\n')
            loaded,inputs=keymap_source(wrapper)
            self.assertEqual(loaded,self.source);self.assertEqual(inputs,[wrapper.resolve(),source.resolve()])
            command=[sys.executable,str(ROOT/'scripts/generate-aml-exclusions.py'),str(wrapper),str(output),'--key-count','41']
            subprocess.run(command,check=True)
            before=output.stat().st_mtime_ns
            subprocess.run(command,check=True)
            self.assertEqual(output.stat().st_mtime_ns,before)
            self.assertEqual(source.read_text(),self.source)
            source.write_text(self.changed(['&none']*41))
            subprocess.run(command,check=True)
            self.assertIn('65535',output.read_text())
    def test_cyclic_wrapper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'cycle.keymap';p.write_text('#include "cycle.keymap"')
            with self.assertRaisesRegex(AssertionError,'cyclic'):
                keymap_source(p)

if __name__ == '__main__':unittest.main()
