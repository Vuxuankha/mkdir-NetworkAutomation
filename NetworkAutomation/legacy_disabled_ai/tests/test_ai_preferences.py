import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from modules import ai_preferences

class PreferencesTests(unittest.TestCase):
    def test_provider_models_saved_independently_without_key(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'prefs.json'
            with patch.dict(os.environ,{'OPENAI_API_KEY':'private-test-key','GEMINI_API_KEY':'another-private-key'}):
                ai_preferences.save('OpenAI','openai-model',path)
                ai_preferences.save('Gemini','gemini-model',path)
            value=ai_preferences.load(path)
            self.assertEqual(value,{'provider':'Gemini','models':{'OpenAI':'openai-model','Gemini':'gemini-model'}})
            self.assertNotIn('private',path.read_text())
            self.assertEqual(list(Path(folder).glob('.ai_preferences_*')),[])
    def test_bad_json_and_shape_use_safe_defaults(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'prefs.json'
            for text in ('{','[]','{"provider":"Unknown"}','{"provider":"Gemini","models":[]}'):
                path.write_text(text)
                self.assertEqual(ai_preferences.load(path)['provider'],'OpenAI')
    def test_invalid_model_leaves_previous_choice(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'prefs.json';ai_preferences.save('OpenAI','model',path)
            for model in ('','bad model','model/escape','x'*161):
                with self.assertRaises(ValueError):ai_preferences.save('OpenAI',model,path)
            self.assertEqual(ai_preferences.load(path)['models']['OpenAI'],'model')
    def test_failed_replace_preserves_old_file_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'prefs.json';ai_preferences.save('OpenAI','old-model',path)
            with patch.object(ai_preferences.os,'replace',side_effect=OSError('access denied')):
                with self.assertRaises(OSError):ai_preferences.save('Gemini','new-model',path)
            self.assertEqual(ai_preferences.load(path)['provider'],'OpenAI')
            self.assertEqual(list(Path(folder).glob('.ai_preferences_*')),[])
    def test_key_status_does_not_expose_value(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'secret-value'}):
            self.assertIn('đã được cấu hình',ai_preferences.key_status('OpenAI'))
            self.assertNotIn('secret-value',ai_preferences.key_status('OpenAI'))

if __name__=='__main__':unittest.main()
