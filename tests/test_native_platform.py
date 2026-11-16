import unittest
from pathlib import Path
from types import SimpleNamespace as Device
from native_platform import data_directory, graphics_backend, output_capture_device


class Platforms(unittest.TestCase):
    def test_data_locations_and_relative_xdg_rejected(self):
        home = Path('/users/example').resolve()
        self.assertEqual(data_directory('darwin', {}, home), home / 'Library/Application Support/FIESTA-Native')
        self.assertEqual(data_directory('linux', {}, home), home / '.local/share/FIESTA-Native')
        self.assertEqual(data_directory('linux', {'XDG_DATA_HOME': 'relative'}, home), home / '.local/share/FIESTA-Native')
        self.assertEqual(data_directory('win32', {'LOCALAPPDATA': str(home / 'AppData/Local')}, home), home / 'AppData/Local/FIESTA-Native')

    def test_graphics(self):
        self.assertEqual([graphics_backend(p) for p in ('win32', 'darwin', 'linux')], ['d3d11', 'metal', 'opengl'])

    def test_linux_selects_only_default_sink_monitor(self):
        mic = Device(id='mic', isloopback=False)
        other = Device(id='headphones.monitor', isloopback=True)
        monitor = Device(id='speakers.monitor', isloopback=True)
        sc = Device(default_speaker=lambda: Device(id='speakers'), all_microphones=lambda **_: [mic, other, monitor])
        self.assertIs(output_capture_device(sc, 'linux'), monitor)
        sc.all_microphones = lambda **_: [mic, other]
        with self.assertRaisesRegex(RuntimeError, 'monitor'):
            output_capture_device(sc, 'linux')

    def test_mac_never_falls_back_to_microphone(self):
        mic = Device(name='MacBook Pro Microphone')
        virtual = Device(name='BlackHole 2ch')
        sc = Device(all_microphones=lambda: [mic, virtual])
        self.assertIs(output_capture_device(sc, 'darwin'), virtual)
        sc.all_microphones = lambda: [mic]
        with self.assertRaisesRegex(RuntimeError, 'BlackHole'):
            output_capture_device(sc, 'darwin')


if __name__ == '__main__':
    unittest.main()
