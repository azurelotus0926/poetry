import json
import re

from .command import Command


TEMPLATE = """[settings]

[repositories]
"""

AUTH_TEMPLATE = """[http-basic]
"""


class ConfigCommand(Command):
    """
    Sets/Gets config options.

    config
        { key : Setting key. }
        { value?* : Setting value. }
        { --list : List configuration settings }
        { --unset : Unset configuration setting }
    """

    help = """This command allows you to edit the poetry config settings and repositories..

To add a repository:

    <comment>poetry repositories.foo https://bar.com/simple/</comment>

To remove a repository (repo is a short alias for repositories):

    <comment>poetry --unset repo.foo</comment>
"""

    def __init__(self):
        from poetry.config import Config

        super(ConfigCommand, self).__init__()

        self._config = Config.create('config.toml')
        self._auth_config = Config.create('auth.toml')

    def initialize(self, i, o):
        super(ConfigCommand, self).initialize(i, o)

        # Create config file if it does not exist
        if not self._config.file.exists():
            self._config.file.parent.mkdir(parents=True, exist_ok=True)
            with self._config.file.open() as f:
                f.write(TEMPLATE)

        if not self._auth_config.file.exists():
            self._auth_config.file.parent.mkdir(parents=True, exist_ok=True)
            with self._auth_config.file.open() as f:
                f.write(AUTH_TEMPLATE)

    def handle(self):
        if self.option('list'):
            self._list_configuration(self._config.raw_content)

            return 0

        setting_key = self.argument('key')
        if not setting_key:
            return 0

        if self.argument('value') and self.option('unset'):
            raise RuntimeError('You can not combine a setting value with --unset')

        # show the value if no value is provided
        if not self.argument('value') and not self.option('unset'):
            m = re.match('^repos?(?:itories)?(?:\.(.+))?', self.argument('key'))
            if m:
                if not m.group(1):
                    value = {}
                    if self._config.setting('repositories') is not None:
                        value = self._config.setting('repositories')
                else:
                    repo = self._config.setting(
                        'repositories.{}'.format(m.group(1))
                    )
                    if repo is None:
                        raise ValueError(
                            'There is no {} repository defined'
                            .format(m.group(1))
                        )

                    value = repo

                self.line(str(value))

            return 0

        values = self.argument('value')

        boolean_validator = lambda val: val in {'true', 'false', '1', '0'}
        boolean_normalizer = lambda val: True if val in ['true', '1'] else False

        unique_config_values = {
            'settings.virtualenvs.create': (boolean_validator, boolean_normalizer),
            'settings.pypi.fallback': (boolean_validator, boolean_normalizer),
        }

        if setting_key in unique_config_values:
            if self.option('unset'):
                return self._remove_single_value(setting_key)

            return self._handle_single_value(
                setting_key,
                unique_config_values[setting_key],
                values
            )

        # handle repositories
        m = re.match('^repos?(?:itories)?(?:\.(.+))?', self.argument('key'))
        if m:
            if not m.group(1):
                raise ValueError('You cannot remove the [repositories] section')

            if self.option('unset'):
                repo = self._config.setting(
                    'repositories.{}'.format(m.group(1))
                )
                if repo is None:
                    raise ValueError(
                        'There is no {} repository defined'.format(m.group(1))
                    )

                self._config.remove_property(
                    'repositories.{}'.format(m.group(1))
                )

                return 0

            if len(values) == 1:
                url = values[0]

                self._config.add_property(
                    'repositories.{}.url'.format(m.group(1)), url
                )

                return 0

            raise ValueError(
                'You must pass the url. '
                'Example: poetry config repositories.foo https://bar.com'
            )

        # handle auth
        m = re.match('^(http-basic)\.(.+)', self.argument('key'))
        if m:
            if self.option('unset'):
                if not self._auth_config.setting('{}.{}'.format(m.group(1), m.group(2))):
                    raise ValueError(
                        'There is no {} {} defined'.format(
                            m.group(2), m.group(1)
                        )
                    )

                self._auth_config.remove_property(
                    '{}.{}'.format(m.group(1), m.group(2))
                )

                return 0

            if m.group(1) == 'http-basic':
                if len(values) == 1:
                    username = values[0]
                    # Only username, so we prompt for password
                    password = self.secret('Password:')
                elif len(values) != 2:
                    raise ValueError(
                        'Expected one or two arguments '
                        '(username, password), got {}'.format(len(values))
                    )
                else:
                    username = values[0]
                    password = values[1]

                self._auth_config.add_property(
                    '{}.{}'.format(m.group(1), m.group(2)),
                    {
                        'username': username,
                        'password': password
                    }
                )

            return 0

        raise ValueError(
            'Setting {} does not exist'.format(self.argument("key"))
        )

    def _handle_single_value(self, key, callbacks, values):
        validator, normalizer = callbacks

        if len(values) > 1:
            raise RuntimeError('You can only pass one value.')

        value = values[0]
        if not validator(value):
            raise RuntimeError(
                '"{}" is an invalid value for {}'.format(value, key)
            )

        self._config.add_property(key, normalizer(value))

        return 0

    def _remove_single_value(self, key):
        self._config.remove_property(key)

        return 0

    def _list_configuration(self, contents, k=None):
        orig_k = k

        for key, value in contents.items():
            if k is None and key not in ['config', 'repositories', 'settings']:
                continue

            if isinstance(value, dict) or key == 'repositories' and k is None:
                if k is None:
                    k = ''

                k += re.sub('^config\.', '', key + '.')
                self._list_configuration(value, k=k)
                k = orig_k

                continue

            if isinstance(value, list):
                value = [
                    json.dumps(val) if isinstance(val, list) else val
                    for val in value
                ]

                value = '[{}]'.format(", ".join(value))

            value = json.dumps(value)

            self.line(
                '[<comment>{}</comment>] <info>{}</info>'.format(
                    (k or "") + key, value
                )
            )
