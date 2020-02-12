from collections import namedtuple
from unittest import mock

import pytest

from detect_secrets_server.core.usage.common.hooks import HookDescriptor
from detect_secrets_server.hooks.external import ExternalHook
from detect_secrets_server.hooks.stdout import StdoutHook
from testing.base_usage_test import UsageTest


class TestOutputOptions(UsageTest):

    def parse_args(self, argument_string=''):
        return super(TestOutputOptions, self).parse_args(
            argument_string,
        )

    @pytest.mark.parametrize(
        'hook_input',
        [
            # No such hook
            'asdf',

            # config file required
            'pysensu',

            # no such file
            'test_data/invalid_file',
        ]
    )
    def test_invalid_output_hook(self, hook_input):
        with pytest.raises(SystemExit):
            self.parse_args('scan --output-hook {} examples -L'.format(hook_input))

    def test_valid_external_hook(self):
        args = self.parse_args(
            'scan --output-hook examples/standalone_hook.py examples -L',
        )
        assert isinstance(args.output_hook, ExternalHook)

    def test_valid_hook_with_config_file(self):
        """
        We don't want test cases to require extra dependencies, only to test
        whether they are compatible. Therefore, we mock ALL_HOOKS with a
        stand-in replacement for a hook that requires a config file.
        """
        with mock.patch(
            'detect_secrets_server.core.usage.common.output.ALL_HOOKS',
            [
                HookDescriptor(
                    display_name='config_needed',
                    module_name='will_be_mocked',
                    class_name='ConfigFileRequiredHook',
                    config_setting=HookDescriptor.CONFIG_REQUIRED,
                ),
            ],
        ), mock.patch(
            'detect_secrets_server.core.usage.common.output.import_module',
            return_value=Module(
                ConfigFileRequiredHook=ConfigFileRequiredMockClass,
            ),
        ):
            args = self.parse_args(
                'scan '
                '--output-hook config_needed '
                '--output-config examples/pysensu.config.yaml '
                'examples '
            )

        with open('examples/pysensu.config.yaml') as f:
            content = f.read()

        assert args.output_hook.config == content

    def test_no_hook_provided(self):
        args = self.parse_args('scan git@git.github.com:Yelp/detect-secrets')
        assert isinstance(args.output_hook, StdoutHook)
        assert args.output_hook_command == ''


Module = namedtuple(
    'Module',
    [
        'ConfigFileRequiredHook',
    ]
)


class ConfigFileRequiredMockClass(object):
    def __init__(self, config):
        self.config = config
