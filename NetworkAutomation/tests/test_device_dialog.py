import sqlite3
import tempfile
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import Mock,patch
from database import db
from modules.device_manager import device_manager
from modules.device_dialog import DeviceEditor,submit_device

class DeviceSaveTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
        (root/'VERSION.txt').write_text('1.4.1')
        self.patches=[patch.object(db,'DB_PATH',root/'devices.db'),patch.object(db,'BASE_DIR',root),patch.object(db,'RESOURCE_DIR',root)]
        for item in self.patches:item.start()
    def tearDown(self):
        for item in reversed(self.patches):item.stop()
        self.temp.cleanup()
    def fields(self,ip='192.0.2.81'):return {'ip':ip,'hostname':' Test PC ','mac':'AA-BB-CC-DD-EE-FF','status':'Unknown'}
    def test_add_persists_and_is_readable(self):
        result,fields=submit_device(self.fields(),device_manager.add_device)
        self.assertTrue(result['success']);saved=device_manager.get_device(result['device_id'])
        self.assertEqual(saved['ip'],fields['ip']);self.assertEqual(saved['hostname'],'Test PC');self.assertEqual(saved['status'],'Unknown')
    def test_duplicate_does_not_overwrite_existing_device(self):
        submit_device(self.fields(),device_manager.add_device)
        values=self.fields();values['hostname']='Another PC'
        result,_=submit_device(values,device_manager.add_device)
        self.assertFalse(result['success']);self.assertIn('đã tồn tại',result['message'])
        self.assertEqual(len(device_manager.get_devices()),1);self.assertEqual(device_manager.get_devices()[0]['hostname'],'Test PC')
    def test_edit_same_ip_updates_existing_row(self):
        result,_=submit_device(self.fields(),device_manager.add_device);device_id=result['device_id']
        fields=self.fields();fields['hostname']='Updated PC';fields['status']='Offline'
        result,_=submit_device(fields,partial(device_manager.edit_device,device_id=device_id))
        self.assertTrue(result['success']);self.assertEqual(device_manager.get_device(device_id)['hostname'],'Updated PC')
    def test_edit_to_duplicate_ip_leaves_original_unchanged(self):
        one,_=submit_device(self.fields(),device_manager.add_device)
        two,_=submit_device(self.fields('192.0.2.82'),device_manager.add_device)
        result,_=submit_device(self.fields(),partial(device_manager.edit_device,device_id=two['device_id']))
        self.assertFalse(result['success']);self.assertEqual(device_manager.get_device(two['device_id'])['ip'],'192.0.2.82')
    def test_invalid_ip_does_not_write(self):
        persist=Mock()
        for ip in ('','not-an-ip','999.1.1.1'):
            with self.assertRaises(ValueError):submit_device(self.fields(ip),persist)
        persist.assert_not_called()
    def test_rejected_save_keeps_dialog_open_for_retry(self):
        editor=DeviceEditor.__new__(DeviceEditor);editor.saving=False;editor.save_button=Mock();editor.window=Mock()
        editor.window.winfo_exists.return_value=True;editor.status=Mock();editor.entries={'ip':Mock()};editor.on_saved=Mock()
        editor.vars={key:Mock(get=Mock(return_value=value)) for key,value in self.fields().items()}
        editor.persist=Mock(return_value={'success':False,'message':'IP đã tồn tại'})
        editor.save();editor.window.destroy.assert_not_called();editor.on_saved.assert_not_called()
        editor.persist.return_value={'success':True};editor.save()
        editor.window.destroy.assert_called_once();editor.on_saved.assert_called_once()
    def test_database_error_keeps_form_open_and_enables_retry(self):
        editor=DeviceEditor.__new__(DeviceEditor);editor.saving=False;editor.save_button=Mock();editor.window=Mock();editor.status=Mock()
        editor.window.winfo_exists.return_value=True;editor.entries={'ip':Mock()};editor.on_saved=Mock()
        editor.vars={key:Mock(get=Mock(return_value=value)) for key,value in self.fields().items()}
        editor.persist=Mock(side_effect=sqlite3.OperationalError('locked'))
        with self.assertLogs('modules.device_dialog',level='ERROR'):editor.save()
        editor.window.destroy.assert_not_called();editor.on_saved.assert_not_called()
        self.assertFalse(editor.saving);editor.save_button.configure.assert_called_with(state='normal')

if __name__=='__main__':unittest.main()
