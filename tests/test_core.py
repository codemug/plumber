from unittest import mock

from mock import MagicMock
import pytest

from plumber.common import ID, DIFF, BRANCH, ACTIVE, TARGET, EXPRESSION, \
  ConfigError, PATH, COMMIT, STEPS, BATCH, TIMEOUT, RETURN_CODE, STDOUT, STDERR, \
  STEP, UTF8, ExecutionFailure, PREHOOK, POSTHOOK, CONDITION, SUCCESS, FAILURE


################################################
# Helpers
################################################


def get_repo_mock():
  repo_mock = MagicMock()
  repo_mock.active_branch = 'master'
  repo_mock.git.checkout.return_value = None
  commits = []
  for commit_id in ['commit-1', 'last-checkpoint']:
    commit_mock = MagicMock()
    commit_mock.__str__.return_value = commit_id
    commits.append(commit_mock)
  repo_mock.iter_commits.return_value = commits
  diffs = []
  for path in ['path1/file1', 'mypath/file1']:
    diff_mock = MagicMock()
    diff_mock.a_rawpath.decode.return_value = path
    diffs.append(diff_mock)
  repo_mock.head.commit.diff.return_value = diffs
  return repo_mock, commits, diffs


################################################
# LocalDiffConditional Tests
################################################


def test_local_diff_conditional_config():
  config = {
    ID: 'conditional',
    DIFF: [],
    BRANCH: {
      ACTIVE: 'master',
      TARGET: 'master'
    },
    EXPRESSION: 'a and b'
  }
  CHECKPOINT = 'checkpoint'
  from plumber.core import LocalDiffConditional
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  assert conditional.id == config[ID]
  assert conditional.active_branch == config[BRANCH][ACTIVE]
  assert conditional.target_branch == config[BRANCH][TARGET]
  assert conditional.checkpoint == CHECKPOINT
  assert conditional.expression == config[EXPRESSION]


def test_local_diff_conditional_config_no_id():
  try:
    config = {
      DIFF: [],
      BRANCH: {
        ACTIVE: 'master',
        TARGET: 'master'
      },
      EXPRESSION: 'a and b'
    }
    CHECKPOINT = 'checkpoint'
    from plumber.core import LocalDiffConditional
    conditional = LocalDiffConditional()
    conditional.configure(config, CHECKPOINT)
  except Exception as e:
    assert type(e) is ConfigError


def test_local_diff_conditional_config_invalid_id():
  try:
    config = {
      ID: ['conditional'],
      DIFF: [],
      BRANCH: {
        ACTIVE: 'master',
        TARGET: 'master'
      },
      EXPRESSION: 'a and b'
    }
    CHECKPOINT = 'checkpoint'
    from plumber.core import LocalDiffConditional
    conditional = LocalDiffConditional()
    conditional.configure(config, CHECKPOINT)
  except Exception as e:
    assert type(e) is ConfigError


def test_local_diff_conditional_config_no_diffs():
  try:
    config = {
      ID: 'conditional',
      BRANCH: {
        ACTIVE: 'master',
        TARGET: 'master'
      },
      EXPRESSION: 'a and b'
    }
    CHECKPOINT = 'checkpoint'
    from plumber.core import LocalDiffConditional
    conditional = LocalDiffConditional()
    conditional.configure(config, CHECKPOINT)
  except Exception as e:
    assert type(e) is ConfigError


def test_local_diff_conditional_config_invalid_diffs():
  try:
    config = {
      ID: 'conditional',
      DIFF: {},
      BRANCH: {
        ACTIVE: 'master',
        TARGET: 'master'
      },
      EXPRESSION: 'a and b'
    }
    CHECKPOINT = 'checkpoint'
    from plumber.core import LocalDiffConditional
    conditional = LocalDiffConditional()
    conditional.configure(config, CHECKPOINT)
  except Exception as e:
    assert type(e) is ConfigError


def test_local_diff_conditional_config_no_active_target_branch():
  config = {
    ID: 'conditional',
    DIFF: [],
    BRANCH: {
    },
    EXPRESSION: 'a and b'
  }
  CHECKPOINT = 'checkpoint'
  from plumber.core import LocalDiffConditional
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  assert conditional.id == config[ID]
  assert conditional.active_branch is None
  assert conditional.target_branch is None
  assert conditional.checkpoint == CHECKPOINT
  assert conditional.expression == config[EXPRESSION]


def test_local_diff_conditional_config_invalid_active_branch():
  try:
    config = {
      ID: 'conditional',
      DIFF: [],
      BRANCH: {
        ACTIVE: ['master'],
        TARGET: 'master'
      },
      EXPRESSION: 'a and b'
    }
    CHECKPOINT = 'checkpoint'
    from plumber.core import LocalDiffConditional
    conditional = LocalDiffConditional()
    conditional.configure(config, CHECKPOINT)
  except Exception as e:
    assert type(e) is ConfigError


def test_local_diff_conditional_config_invalid_target_branch():
  try:
    config = {
      ID: 'conditional',
      DIFF: [],
      BRANCH: {
        ACTIVE: 'master',
        TARGET: ['master']
      },
      EXPRESSION: 'a and b'
    }
    CHECKPOINT = 'checkpoint'
    from plumber.core import LocalDiffConditional
    conditional = LocalDiffConditional()
    conditional.configure(config, CHECKPOINT)
  except Exception as e:
    assert type(e) is ConfigError


def test_local_diff_conditional_config_invalid_expression():
  try:
    config = {
      ID: 'conditional',
      DIFF: [],
      BRANCH: {
        ACTIVE: 'master',
        TARGET: 'master'
      },
      EXPRESSION: ['a and b']
    }
    CHECKPOINT = 'checkpoint'
    from plumber.core import LocalDiffConditional
    conditional = LocalDiffConditional()
    conditional.configure(config, CHECKPOINT)
  except Exception as e:
    assert type(e) is ConfigError


def test_local_diff_conditional_evaluate():
  config = {
    ID: 'conditional',
    DIFF: [{
      ID: 'a',
      PATH: 'mypath/.*'
    }],
    BRANCH: {
      ACTIVE: 'master',
      TARGET: 'testing'
    }
  }
  CHECKPOINT = {COMMIT: 'last-checkpoint'}
  from plumber.core import LocalDiffConditional
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  conditional.repo, commits, diffs = get_repo_mock()

  result = conditional.evaluate()
  assert result is True
  conditional.repo.git.checkout.assert_called()
  conditional.repo.git.checkout.assert_any_call('testing')
  conditional.repo.git.checkout.assert_any_call('master')
  for commit in commits:
    commit.__str__.assert_called()
  conditional.repo.iter_commits.assert_called_once()
  for diff in diffs:
    diff.a_rawpath.decode.assert_called()
  conditional.repo.head.commit.diff.assert_called()


def test_local_diff_conditional_evaluate_not_active_branch():
  config = {
    ID: 'conditional',
    DIFF: [{
      ID: 'a',
      PATH: 'mypath/.*'
    }],
    BRANCH: {
      ACTIVE: 'testing',
      TARGET: 'testing'
    }
  }
  CHECKPOINT = {COMMIT: 'last-checkpoint'}
  from plumber.core import LocalDiffConditional
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  conditional.repo = MagicMock()
  conditional.repo.active_branch = 'master'

  assert conditional.evaluate() is False


def test_local_diff_conditional_evaluate_no_checkpoint():
  config = {
    ID: 'conditional',
    DIFF: [{
      ID: 'a',
      PATH: 'mypath/.*'
    }]
  }
  CHECKPOINT = {}
  from plumber.core import LocalDiffConditional
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  assert conditional.evaluate() is True


def test_local_diff_conditional_evaluate_invalid_diff():
  config = {
    ID: 'conditional',
    DIFF: ['mypath/.*']
  }
  CHECKPOINT = {COMMIT: 'last-checkpoint'}
  from plumber.core import LocalDiffConditional
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  conditional.repo, commits, diffs = get_repo_mock()

  try:
    _ = conditional.evaluate()
    pytest.fail('Conditional should not evaluate on invalid diff spec')
  except Exception as e:
    assert type(e) is ConfigError


def test_local_diff_conditional_evaluate_invalid_diff_path():
  config = {
    ID: 'conditional',
    DIFF: [{
      ID: 'a',
      'file': 'mypath/.*'
    }]
  }
  CHECKPOINT = {COMMIT: 'last-checkpoint'}
  from plumber.core import LocalDiffConditional
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  conditional.repo, commits, diffs = get_repo_mock()
  assert conditional.evaluate() is False


def test_local_diff_conditional_evaluate_invalid_diff_expression_id():
  config = {
    ID: 'conditional',
    EXPRESSION: 'a',
    DIFF: [{
      ID: 'b',
      'file': 'mypath/.*'
    }]
  }
  CHECKPOINT = {COMMIT: 'last-checkpoint'}
  from plumber.core import LocalDiffConditional
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  conditional.repo, commits, diffs = get_repo_mock()

  try:
    _ = conditional.evaluate()
    pytest.fail('Conditional should not evaluate on undefined diff id')
  except Exception as e:
    assert type(e) is NameError


def test_local_diff_conditional_evaluate_multiple_with_expression():
  config = {
    ID: 'conditional',
    EXPRESSION: 'a and b',
    DIFF: [{
      ID: 'a',
      PATH: 'mypath/.*'
    }, {
      ID: 'b',
      PATH: 'path1/.*'
    }]
  }
  CHECKPOINT = {COMMIT: 'last-checkpoint'}
  from plumber.core import LocalDiffConditional
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  conditional.repo, commits, diffs = get_repo_mock()
  assert conditional.evaluate() is True


def test_local_diff_conditional_create_checkpoint():
  config = {
    ID: 'conditional',
    EXPRESSION: 'a and b',
    DIFF: [{
      ID: 'a',
      PATH: 'mypath/.*'
    }, {
      ID: 'b',
      PATH: 'path1/.*'
    }]
  }
  CHECKPOINT = {COMMIT: 'last-checkpoint'}
  from plumber.core import LocalDiffConditional
  from git import Repo
  conditional = LocalDiffConditional()
  conditional.configure(config, CHECKPOINT)
  new_checkpoint = conditional.create_checkpoint()
  assert COMMIT in new_checkpoint
  assert new_checkpoint[COMMIT] == str(Repo().head.commit)


################################################
# Executor Tests
################################################


def test_executor_configure():
  CONFIG = {
    STEPS: [
      'echo "Hello"',
      'echo "World"'
    ],
    BATCH: False,
    TIMEOUT: 100
  }
  from plumber.core import Executor
  executor = Executor()
  executor.configure(CONFIG)
  assert executor.steps[0] == CONFIG[STEPS][0]
  assert executor.steps[1] == CONFIG[STEPS][1]
  assert executor.batch is False
  assert executor.timeout == 100
  assert executor.results is not None


def test_executor_configure_no_steps():
  from plumber.core import Executor
  executor = Executor()
  try:
    executor.configure({})
    pytest.fail('Executor should not be configured without steps')
  except Exception as e:
    assert type(e) is ConfigError


def test_executor_configure_invalid_steps():
  from plumber.core import Executor
  executor = Executor()
  try:
    executor.configure({STEPS: {'step 1': 'step 1'}})
    pytest.fail('Executor should not be configured without right steps')
  except Exception as e:
    assert type(e) is ConfigError


def test_executor_configure_invalid_batch():
  CONFIG = {
    STEPS: [
      'echo "Hello"',
      'echo "World"'
    ],
    BATCH: 'False',
    TIMEOUT: 100
  }
  from plumber.core import Executor
  executor = Executor()
  try:
    executor.configure(CONFIG)
  except Exception as e:
    assert type(e) is ConfigError


def test_executor_configure_invalid_timeout():
  CONFIG = {
    STEPS: [
      'echo "Hello"',
      'echo "World"'
    ],
    BATCH: False,
    TIMEOUT: '100'
  }
  from plumber.core import Executor
  executor = Executor()
  try:
    executor.configure(CONFIG)
  except Exception as e:
    assert type(e) is ConfigError


def test_executor_execute():
  CONFIG = {
    STEPS: [
      'echo "Hello"',
      'echo "World"'
    ],
    BATCH: False,
  }
  from plumber.core import Executor
  executor = Executor()
  executor.configure(CONFIG)
  executor.execute()
  assert len(executor.results) == 2
  assert executor.results[0][RETURN_CODE] == 0
  assert executor.results[0][STDOUT].decode(UTF8) == 'Hello\n'
  assert executor.results[0][STDERR].decode(UTF8) == ''
  assert executor.results[0][STEP] == 'echo "Hello"'
  assert executor.results[1][RETURN_CODE] == 0
  assert executor.results[1][STDOUT].decode(UTF8) == 'World\n'
  assert executor.results[1][STDERR].decode(UTF8) == ''
  assert executor.results[1][STEP] == 'echo "World"'


def test_executor_execute_batch():
  CONFIG = {
    STEPS: [
      'echo "Hello"',
      'echo "World"'
    ],
    BATCH: True,
  }
  from plumber.core import Executor
  executor = Executor()
  executor.configure(CONFIG)
  executor.execute()
  assert len(executor.results) == 1
  assert executor.results[0][RETURN_CODE] == 0
  assert executor.results[0][STDOUT].decode(UTF8) == 'Hello\nWorld\n'
  assert executor.results[0][STDERR].decode(UTF8) == ''
  assert executor.results[0][STEP] == '\n echo "Hello"\n echo "World"'


def test_executor_execute_error():
  CONFIG = {
    STEPS: [
      'echi "Hello"',
      'echo "World"'
    ],
    BATCH: False,
  }
  from plumber.core import Executor
  executor = Executor()
  executor.configure(CONFIG)
  try:
    executor.execute()
    pytest.fail('Executor should raise exception on invalid command')
  except Exception as e:
    assert type(e) is ExecutionFailure

  assert len(executor.results) == 1
  assert executor.results[0][RETURN_CODE] != 0
  assert executor.results[0][STDOUT].decode(UTF8) == ''
  assert executor.results[0][STDERR].decode(UTF8) != ''
  assert executor.results[0][STEP] == 'echi "Hello"'


def test_executor_execute_error_timeout():
  CONFIG = {
    STEPS: [
      'sleep 2',
      'echo "World"'
    ],
    TIMEOUT: 1,
    BATCH: False,
  }
  from plumber.core import Executor
  executor = Executor()
  executor.configure(CONFIG)
  try:
    executor.execute()
    pytest.fail('Executor should raise timeout exception if timeout is set')
  except Exception as e:
    assert type(e) is ExecutionFailure

  assert len(executor.results) == 1
  assert executor.results[0][RETURN_CODE] == 130
  assert executor.results[0][STDOUT].decode(UTF8) == ''
  assert executor.results[0][STDERR].decode(UTF8) != ''
  assert executor.results[0][STEP] == 'sleep 2'


def test_executor_execute_batch_error():
  CONFIG = {
    STEPS: [
      'echo "Hello"',
      'echoi "World"'
    ],
    BATCH: True,
  }
  from plumber.core import Executor
  executor = Executor()
  executor.configure(CONFIG)
  try:
    executor.execute()
  except Exception as e:
    assert type(e) is ExecutionFailure
  assert len(executor.results) == 1
  assert executor.results[0][RETURN_CODE] != 0
  assert executor.results[0][STDOUT].decode(UTF8) == 'Hello\n'
  assert executor.results[0][STDERR].decode(UTF8) != ''
  assert executor.results[0][STEP] == '\n echo "Hello"\n echoi "World"'


def test_executor_execute_get_results():
  CONFIG = {
    STEPS: [
      'echo "Hello"',
      'echo "World"'
    ],
    BATCH: False,
  }
  from plumber.core import Executor
  executor = Executor()
  executor.configure(CONFIG)
  assert len(executor.get_results()) == 0
  executor.execute()
  assert len(executor.get_results()) == 2
  assert executor.get_results()[0][RETURN_CODE] == 0
  assert executor.get_results()[0][STDOUT].decode(UTF8) == 'Hello\n'
  assert executor.get_results()[0][STDERR].decode(UTF8) == ''
  assert executor.get_results()[0][STEP] == 'echo "Hello"'
  assert executor.get_results()[1][RETURN_CODE] == 0
  assert executor.get_results()[1][STDOUT].decode(UTF8) == 'World\n'
  assert executor.get_results()[1][STDERR].decode(UTF8) == ''
  assert executor.get_results()[1][STEP] == 'echo "World"'


################################################
# Hooked Tests
################################################

HOOKS_CONFIG = {
  PREHOOK: [
    {
      STEPS: [
        'echo "prehook"'
      ]
    }
  ],
  POSTHOOK: [
    {
      STEPS: [
        'echo "posthook"'
      ]
    },
    {
      CONDITION: SUCCESS,
      STEPS: [
        'echo "posthook-success"'
      ]
    },
    {
      CONDITION: FAILURE,
      STEPS: [
        'echo "posthook-failure"'
      ]
    }
  ]
}


def test_hooked_configure():
  from plumber.core import Hooked, Executor
  hooks = Hooked()
  hooks.configure(HOOKS_CONFIG)
  assert hooks.prehooks is not None
  assert len(hooks.prehooks) == 1
  assert type(hooks.prehooks[0]) is Executor
  assert hooks.prehooks[0].steps[0] == 'echo "prehook"'
  assert hooks.posthooks is not None
  assert len(hooks.posthooks) == 1
  assert type(hooks.posthooks[0]) is Executor
  assert hooks.posthooks[0].steps[0] == 'echo "posthook"'
  assert hooks.posthooks_success is not None
  assert len(hooks.posthooks_success) == 1
  assert type(hooks.posthooks_success[0]) is Executor
  assert hooks.posthooks_success[0].steps[0] == 'echo "posthook-success"'
  assert hooks.posthooks_failure is not None
  assert len(hooks.posthooks_failure) == 1
  assert type(hooks.posthooks_failure[0]) is Executor
  assert hooks.posthooks_failure[0].steps[0] == 'echo "posthook-failure"'


def test_hooked_configure_invalid_prehooks():
  hooks_config = {
    PREHOOK: 'echo "prehook"'
  }
  from plumber.core import Hooked
  hooks = Hooked()
  try:
    hooks.configure(hooks_config)
  except Exception as e:
    assert type(e) is ConfigError


def test_hooked_configure_invalid_posthooks():
  hooks_config = {
    POSTHOOK: 'echo "prehook"'
  }
  from plumber.core import Hooked
  hooks = Hooked()
  try:
    hooks.configure(hooks_config)
  except Exception as e:
    assert type(e) is ConfigError


def test_hooked_run_prehooks():
  from plumber.core import Hooked
  hooks = Hooked()
  hooks.configure(HOOKS_CONFIG)
  hooks.run_prehooks()
  for executor in hooks.prehooks:
    assert len(executor.results) == 1
    assert executor.results[0][RETURN_CODE] == 0
    assert executor.results[0][STDOUT].decode(UTF8) == 'prehook\n'
    assert executor.results[0][STDERR].decode(UTF8) == ''
    assert executor.results[0][STEP] == 'echo "prehook"'


def test_hooked_run_posthooks():
  from plumber.core import Hooked
  hooks = Hooked()
  hooks.configure(HOOKS_CONFIG)
  hooks.run_posthooks('None')
  for executor in hooks.posthooks:
    assert len(executor.results) == 1
    assert executor.results[0][RETURN_CODE] == 0
    assert executor.results[0][STDOUT].decode(UTF8) == 'posthook\n'
    assert executor.results[0][STDERR].decode(UTF8) == ''
    assert executor.results[0][STEP] == 'echo "posthook"'
  for executor in hooks.posthooks_success:
    assert len(executor.results) == 0
  for executor in hooks.posthooks_failure:
    assert len(executor.results) == 0


def test_hooked_run_posthooks_success():
  from plumber.core import Hooked
  hooks = Hooked()
  hooks.configure(HOOKS_CONFIG)
  hooks.run_posthooks(SUCCESS)
  for executor in hooks.posthooks:
    assert len(executor.results) == 1
    assert executor.results[0][RETURN_CODE] == 0
    assert executor.results[0][STDOUT].decode(UTF8) == 'posthook\n'
    assert executor.results[0][STDERR].decode(UTF8) == ''
    assert executor.results[0][STEP] == 'echo "posthook"'
  for executor in hooks.posthooks_success:
    assert len(executor.results) == 1
    assert executor.results[0][RETURN_CODE] == 0
    assert executor.results[0][STDOUT].decode(UTF8) == 'posthook-success\n'
    assert executor.results[0][STDERR].decode(UTF8) == ''
    assert executor.results[0][STEP] == 'echo "posthook-success"'
  for executor in hooks.posthooks_failure:
    assert len(executor.results) == 0


def test_hooked_run_posthooks_failure():
  from plumber.core import Hooked
  hooks = Hooked()
  hooks.configure(HOOKS_CONFIG)
  hooks.run_posthooks(FAILURE)
  for executor in hooks.posthooks:
    assert len(executor.results) == 1
    assert executor.results[0][RETURN_CODE] == 0
    assert executor.results[0][STDOUT].decode(UTF8) == 'posthook\n'
    assert executor.results[0][STDERR].decode(UTF8) == ''
    assert executor.results[0][STEP] == 'echo "posthook"'
  for executor in hooks.posthooks_failure:
    assert len(executor.results) == 1
    assert executor.results[0][RETURN_CODE] == 0
    assert executor.results[0][STDOUT].decode(UTF8) == 'posthook-failure\n'
    assert executor.results[0][STDERR].decode(UTF8) == ''
    assert executor.results[0][STEP] == 'echo "posthook-failure"'
  for executor in hooks.posthooks_success:
    assert len(executor.results) == 0


def test_hooked_wrap_in_hooks_success():
  from plumber.core import Hooked
  hooks = Hooked()
  hooks.configure(HOOKS_CONFIG)

  def check_prehook_called():
    for executor in hooks.prehooks:
      assert len(executor.results) == 1
      assert executor.results[0][RETURN_CODE] == 0
      assert executor.results[0][STDOUT].decode(UTF8) == 'prehook\n'
      assert executor.results[0][STDERR].decode(UTF8) == ''
      assert executor.results[0][STEP] == 'echo "prehook"'
    for executor in hooks.posthooks:
      assert len(executor.results) == 0
    for executor in hooks.posthooks_success:
      assert len(executor.results) == 0
    for executor in hooks.posthooks_failure:
      assert len(executor.results) == 0
    return 'success'

  def check_posthook_called(status):
    assert status == SUCCESS
    for executor in hooks.posthooks:
      assert len(executor.results) == 1
      assert executor.results[0][RETURN_CODE] == 0
      assert executor.results[0][STDOUT].decode(UTF8) == 'posthook\n'
      assert executor.results[0][STDERR].decode(UTF8) == ''
      assert executor.results[0][STEP] == 'echo "posthook"'
    for executor in hooks.posthooks_success:
      assert len(executor.results) == 1
      assert executor.results[0][RETURN_CODE] == 0
      assert executor.results[0][STDOUT].decode(UTF8) == 'posthook-success\n'
      assert executor.results[0][STDERR].decode(UTF8) == ''
      assert executor.results[0][STEP] == 'echo "posthook-success"'
    for executor in hooks.posthooks_failure:
      assert len(executor.results) == 0

  assert hooks.wrap_in_hooks(check_prehook_called,
                             check_posthook_called)() == 'success'


def test_hooked_wrap_in_hooks_failure():
  from plumber.core import Hooked
  hooks = Hooked()
  hooks.configure(HOOKS_CONFIG)

  def check_prehook_called():
    for executor in hooks.prehooks:
      assert len(executor.results) == 1
      assert executor.results[0][RETURN_CODE] == 0
      assert executor.results[0][STDOUT].decode(UTF8) == 'prehook\n'
      assert executor.results[0][STDERR].decode(UTF8) == ''
      assert executor.results[0][STEP] == 'echo "prehook"'
    for executor in hooks.posthooks:
      assert len(executor.results) == 0
    for executor in hooks.posthooks_success:
      assert len(executor.results) == 0
    for executor in hooks.posthooks_failure:
      assert len(executor.results) == 0
    raise ExecutionFailure('Just to test')

  def check_posthook_called(status):
    assert status == FAILURE
    for executor in hooks.posthooks:
      assert len(executor.results) == 1
      assert executor.results[0][RETURN_CODE] == 0
      assert executor.results[0][STDOUT].decode(UTF8) == 'posthook\n'
      assert executor.results[0][STDERR].decode(UTF8) == ''
      assert executor.results[0][STEP] == 'echo "posthook"'
    for executor in hooks.posthooks_failure:
      assert len(executor.results) == 1
      assert executor.results[0][RETURN_CODE] == 0
      assert executor.results[0][STDOUT].decode(UTF8) == 'posthook-failure\n'
      assert executor.results[0][STDERR].decode(UTF8) == ''
      assert executor.results[0][STEP] == 'echo "posthook-failure"'
    for executor in hooks.posthooks_success:
      assert len(executor.results) == 0

  try:
    hooks.wrap_in_hooks(check_prehook_called, check_posthook_called)()
  except Exception as e:
    assert type(e) is ExecutionFailure


################################################
# PlumberPipe Tests
################################################


def test_pipe_configure():
  pass


def test_pipe_configure_no_id():
  pass


def test_pipe_configure_invalid_id():
  pass


def test_pipe_configure_no_conditions():
  pass


def test_pipe_configure_invalid_conditions():
  pass


def test_pipe_configure_invalid_conditions_id():
  pass


def test_pipe_configure_invalid_conditions_id_duplicate():
  pass


def test_pipe_configure_no_actions():
  pass


def test_pipe_configure_invalid_actions():
  pass


def test_pipe_evaluate():
  pass


def test_pipe_evaluate_expression():
  pass


def test_pipe_execute():
  pass


def test_pipe_get_new_checkpoint():
  pass


def test_pipe_run_prehooks():
  pass


def test_pipe_run_posthooks():
  pass


################################################
# PlumberPlanner Tests
################################################


def test_planner_init():
  pass


def test_planner_init_no_global_config():
  pass


def test_planner_init_no_checkpointing_config():
  pass


def test_planner_init_no_pipes():
  pass


def test_planner_init_pipes_no_id():
  pass


def test_planner_init_pipes_duplicate_id():
  pass


def test_planner_run_prehooks():
  pass


def test_planner_run_posthooks():
  pass


def test_planner_get_analysis_report():
  pass


def test_planner_execute():
  pass


def test_planner_execute_error():
  pass


################################################
# Functions Tests
################################################


def test_create_conditional():
  pass


def test_create_conditional_default():
  pass


def test_create_conditional_invalid():
  pass


def test_create_execution_report():
  pass


def test_create_execution_report_gitmoji():
  pass


def test_create_initial_report():
  pass


def test_contains_activity():
  pass


def test_wrap_in_dividers():
  pass
