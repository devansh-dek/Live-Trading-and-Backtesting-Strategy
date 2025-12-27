class BaseStrategy:
    def generate_entry_signal(self, df):
        raise NotImplementedError

    def generate_exit_signal(self, df):
        raise NotImplementedError
