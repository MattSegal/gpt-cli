import click


class DefaultCommandGroup(click.Group):
    """allow a default command for a group"""

    def command(self, *args, **kwargs):
        default_command = kwargs.pop("default_command", False)
        if default_command and not args:
            kwargs["name"] = kwargs.get("name", "<default>")
        decorator = super(DefaultCommandGroup, self).command(*args, **kwargs)

        if default_command:

            def new_decorator(f):
                cmd = decorator(f)
                self.default_command = cmd.name
                return cmd

            return new_decorator

        return decorator

    def resolve_command(self, ctx, args):
        try:
            # Test if the command parses
            return super(DefaultCommandGroup, self).resolve_command(ctx, args)
        except click.UsageError:
            # Command did not parse, assume it is the default command
            param_args = []
            for k, v in ctx.params.items():
                if v:
                    param_args.append(f"--{k}")

            args = [self.default_command, *param_args, *args]
            return super(DefaultCommandGroup, self).resolve_command(ctx, args)


@click.group(cls=DefaultCommandGroup)
def cli():
    """
    Ask your language model a question.

    \b
    Examples:
      ask how do I flatten a list in python
      ask ffmpeg convert webm to a gif
      ask what is the best restaurant in melbourne
      echo 'hello world' | ask what does this text say
      ask web http://example.com | ask what does this website say

    """
    pass
