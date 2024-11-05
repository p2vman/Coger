import os
import json


class CogContext:
    def __init__(self, bot, raw):
        self.bot = bot
        self.raw = raw

    def Rew(self, raw):
        return CogContext(self.bot, raw)

    def add(self, cog):
        self.bot.add_cog(cog)


class CogLoader:
    def __init__(self, bot):
        self.bot = bot

    def load(self, dir_: str):
        base_ctx = CogContext(self.bot, {})

        for filename in os.listdir(dir_):
            if filename.endswith("_c.py"):
                with open(os.path.join(dir_, filename), 'r', encoding='utf-8') as file:
                    namespace = {}
                    exec(file.read(), namespace)
                    class_dict = {name: obj for name, obj in namespace.items() if isinstance(obj, type)}
                    func_dict = {name: obj for name, obj in namespace.items() if callable(obj)}

                    json_filepath = os.path.join(dir_, f"{filename[:-5]}.json")
                    if os.path.exists(json_filepath):
                        with open(json_filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for entry in data:
                                ctx = base_ctx.Rew(entry['raw'])
                                if entry['name'] in func_dict and ('type' in entry and entry['type'] == 0):
                                    func_dict[entry['name']](ctx)
                                elif entry['name'] in class_dict:
                                    ins = class_dict[entry['name']](ctx)
                                    if 'load' in entry and entry['load']:
                                        ctx.add(ins)
                                    ins.init(ctx)
                            continue

                    else:
                        if filename[:-5] in class_dict:
                            class_dict[filename[:-5]](base_ctx).init(base_ctx)
                            continue

