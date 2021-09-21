class InvalidInitException(Exception):
    """
    Your init.yml is bad and you should feel bad.
    """

    def __init__(self, message):
        super().__init__(message)


class ConfigNode:
    """
    A wrapper around a YAML configuration object for easier use.

    Consider the following YAML object, stored in a ConfigNode "node":

    output_prefix_length: 5
    test_cases: [
        {
            batched: [
                {
                    in: ruby.1.in
                },
                {
                    in: ruby.2.in,
                    output_prefix_length: 0,
                }
            ],
            out: ruby.out,
            points: 10
        },
        {
            in: ruby.4.in,
            out: ruby.4.out,
            points: 15
        }
    ]

    node.test_cases[0].batched[0]['in'] == 'ruby.1.in'
    node.test_cases[0].batched[0].out == 'ruby.out'
    node.test_cases[0].batched[0].points == 10
    node.test_cases[1].points == 15
    node.test_cases[1].output_prefix_length == 5
    node.test_cases[0].batched[0].output_prefix_length == 5
    node.test_cases[0].batched[1].output_prefix_length == 0
    """

    def __init__(self, raw_config=None, parent=None, defaults=None, dynamic=True):
        self.dynamic = dynamic
        if defaults:
            self.raw_config = defaults
            self.raw_config.update(raw_config or {})
        else:
            self.raw_config = raw_config or {}
        self.parent = parent

    def unwrap(self):
        return self.raw_config

    def update(self, dct):
        if hasattr(self.raw_config, 'update'):
            self.raw_config.update(dct)
        else:
            raise InvalidInitException('config node is not a dict')

    def keys(self):
        if hasattr(self.raw_config, 'keys'):
            return self.raw_config.keys()
        raise InvalidInitException('config node is not a dict')

    def get(self, key, default=None):
        return self[key] if key in self else default

    def items(self):
        return self.iteritems()

    def iteritems(self):
        if not hasattr(self.raw_config, 'items'):
            raise InvalidInitException('config node is not a dict')
        for key, value in self.raw_config.items():
            should_wrap = isinstance(value, list) or isinstance(value, dict)
            yield key, ConfigNode(value, self, dynamic=self.dynamic) if should_wrap else value

    def __getattr__(self, item):
        return self[item.replace('_', '-')] if self[item] is None else self[item]

    def __getitem__(self, item):
        try:
            if self.dynamic and isinstance(self.raw_config, dict):

                def run_dynamic_key(dynamic_key, run_func):
                    # Wrap in a ConfigNode so dynamic keys can benefit from the nice features of ConfigNode
                    local = {'node': ConfigNode(self.raw_config.get(item, {}), self)}
                    try:
                        cfg = run_func(self.raw_config[dynamic_key], local)
                    except Exception as e:
                        import traceback

                        traceback.print_exc()
                        raise InvalidInitException(
                            'exception executing dynamic key ' + str(dynamic_key) + ': ' + str(e)
                        )
                    del self.raw_config[dynamic_key]
                    self.raw_config[item] = cfg

                if item + '++' in self.raw_config:

                    def full(code, local):
                        exec(code, local)
                        return local['node']

                    run_dynamic_key(item + '++', full)
                elif item + '+' in self.raw_config:
                    run_dynamic_key(item + '+', lambda code, local: eval(code, local))

            cfg = self.raw_config[item]
            if isinstance(cfg, list) or isinstance(cfg, dict):
                cfg = ConfigNode(cfg, self, dynamic=self.dynamic)
        except (KeyError, IndexError, TypeError):
            cfg = self.parent[item] if self.parent else None
        return cfg

    def __len__(self):
        return len(self.raw_config)

    def __setitem__(self, item, value):
        self.raw_config[item] = value

    def __iter__(self):
        for cfg in self.raw_config:
            if isinstance(cfg, list) or isinstance(cfg, dict):
                cfg = ConfigNode(cfg, self, dynamic=self.dynamic)
            yield cfg

    def __str__(self):
        return '<ConfigNode(%s)>' % str(self.raw_config)

    def __add__(self, other):
        if isinstance(other, (list, dict)):
            return self.raw_config + other
        elif isinstance(other, ConfigNode):
            return ConfigNode(self.raw_config + other.raw_config, None, dynamic=self.dynamic)
        else:
            return NotImplemented

    def __radd__(self, other):
        if isinstance(other, (list, dict)):
            return other + self.raw_config
        else:
            return NotImplemented
