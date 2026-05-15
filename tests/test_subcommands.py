from __future__ import annotations

from .conftest import run_nlp


class TestRegisterUnregister:
    def test_register_model(self, nlp_config_dir, model_file):
        result = run_nlp("model", "register", "test-model", str(model_file), nlp_config_dir=nlp_config_dir)
        assert result.returncode == 0
        assert "Registered model" in result.stdout
        assert "test-model" in result.stdout

    def test_register_nonexistent_path(self, nlp_config_dir):
        result = run_nlp("model", "register", "bad", "/nonexistent/model.gguf", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 1
        assert "File not found" in result.stderr

    def test_register_duplicate(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "dup", str(model_file), nlp_config_dir=nlp_config_dir)
        result = run_nlp("model", "register", "dup", str(model_file), nlp_config_dir=nlp_config_dir)
        assert result.returncode == 1
        assert "already registered" in result.stderr

    def test_unregister_model(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "to-unreg", str(model_file), nlp_config_dir=nlp_config_dir)
        result = run_nlp("model", "unregister", "to-unreg", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 0
        assert "Unregistered model" in result.stdout

    def test_unregister_nonexistent(self, nlp_config_dir):
        result = run_nlp("model", "unregister", "ghost", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 1
        assert "not found" in result.stderr


class TestModels:
    def test_models_empty(self, nlp_config_dir):
        result = run_nlp("model", "list", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 0
        assert "No models registered" in result.stdout

    def test_models_list(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "m1", str(model_file), nlp_config_dir=nlp_config_dir)
        result = run_nlp("model", "list", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 0
        assert "Registered models" in result.stdout
        assert "m1" in result.stdout


class TestProfilesSubcommand:
    def test_profiles_empty(self, nlp_config_dir):
        result = run_nlp("profile", "list", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 0
        assert "No profiles created" in result.stdout

    def test_profiles_list(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "pmodel", str(model_file), nlp_config_dir=nlp_config_dir)
        run_nlp("profile", "create", "pprofile", "--model", "pmodel", nlp_config_dir=nlp_config_dir)
        result = run_nlp("profile", "list", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 0
        assert "pprofile" in result.stdout


class TestProfileCreate:
    def test_profile_create(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "pc-model", str(model_file), nlp_config_dir=nlp_config_dir)
        result = run_nlp("profile", "create", "pc", "--model", "pc-model", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 0
        assert "Created profile" in result.stdout
        assert "pc" in result.stdout

    def test_profile_create_unknown_model(self, nlp_config_dir):
        result = run_nlp("profile", "create", "badpc", "--model", "no-such-model", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 1
        assert "Unknown model" in result.stderr

    def test_profile_create_duplicate(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "dup-model", str(model_file), nlp_config_dir=nlp_config_dir)
        run_nlp("profile", "create", "dupp", "--model", "dup-model", nlp_config_dir=nlp_config_dir)
        result = run_nlp("profile", "create", "dupp", "--model", "dup-model", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 1
        assert "already exists" in result.stderr

    def test_profile_create_with_system_prompt(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "sp-model", str(model_file), nlp_config_dir=nlp_config_dir)
        result = run_nlp(
            "profile", "create", "sp-p", "--model", "sp-model",
            "--system-prompt", "You are a helpful assistant.",
            nlp_config_dir=nlp_config_dir,
        )
        assert result.returncode == 0
        assert "Created profile" in result.stdout

    def test_profile_create_with_args(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "args-model", str(model_file), nlp_config_dir=nlp_config_dir)
        result = run_nlp(
            "profile", "create", "args-p", "--model", "args-model",
            "--args", "--temp 0.7 --ctx-size 2048",
            nlp_config_dir=nlp_config_dir,
        )
        assert result.returncode == 0
        assert "Created profile" in result.stdout


class TestProfileShowDelete:
    def test_profile_show(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "show-model", str(model_file), nlp_config_dir=nlp_config_dir)
        run_nlp("profile", "create", "show-p", "--model", "show-model", nlp_config_dir=nlp_config_dir)
        result = run_nlp("profile", "show", "show-p", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 0
        assert "show-p" in result.stdout
        assert "show-model" in result.stdout

    def test_profile_delete(self, nlp_config_dir, model_file):
        run_nlp("model", "register", "del-model", str(model_file), nlp_config_dir=nlp_config_dir)
        run_nlp("profile", "create", "del-p", "--model", "del-model", nlp_config_dir=nlp_config_dir)
        result = run_nlp("profile", "delete", "del-p", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 0
        assert "Deleted profile" in result.stdout

    def test_profile_delete_nonexistent(self, nlp_config_dir):
        result = run_nlp("profile", "delete", "nope", nlp_config_dir=nlp_config_dir)
        assert result.returncode == 1
        assert "not found" in result.stderr
