import os

class PromptBuilder:
    def __init__(self, role, article=None, chat_history=None):
        self.role = (role or '').strip()
        self.article = (article or '').strip()
        self.chat_history = chat_history or []

        if os.path.exists(self.role):
            with open(self.role, 'r', encoding='utf-8') as f:
                self.role = f.read()

    def get_role(self, sender):
        return 'user' if sender else 'assistant'

    def build_system_part(self, article=None):
        system_parts = []
        if self.role:
            system_parts.append(self.role)
        if article:
            if system_parts:
                system_parts.append(r"""
                
                    -------\n\n
                
                """)
            system_parts.append(f"""
                ### Artikel:
                {article}
            """)
        return system_parts

    def get_chatml_prompt(self, article=None, chat_history=None):
        article = article or self.article
        chat_history = chat_history or self.chat_history

        messages = []
        system_parts = self.build_system_part(article)
        if system_parts:
            messages.append({
                'role': 'system',
                'content': "\n\n".join(system_parts)
            })

        for entry in chat_history:
            messages.append({
                'role': self.get_role(entry['senderId']),
                'content': entry['message'].strip()
            })

        return messages

    def get_qwen_prompt(self, article=None, chat_history=None):
        article = article or self.article
        chat_history = chat_history or self.chat_history

        history = [
            f"""
                <|im_start|>{self.get_role(entry['senderId'])}
                    {entry['message'].strip()}
                <|im_end|>
            """
            for entry in chat_history
        ]

        system_parts = self.build_system_part(article)
        if system_parts:
            system_parts = [
                "<|im_start|>system",
                *system_parts,
                "<|im_end|>"
            ]

        return "\n\n".join([
            "\n".join(system_parts),
            "\n".join(history),
            "<|im_start|>assistant"
        ])

    def get_plain_prompt(self, article=None, chat_history=None):
        article = article or self.article
        chat_history = chat_history or self.chat_history

        history = [
            f"""
                ### {self.get_role(entry['senderId'])}:
                {entry['message'].strip()}
            """
            for entry in chat_history
        ]
        if history:
            history = [
                "## Riwayat percakapan:",
                *history
            ]

        system_parts = self.build_system_part(article)
        if system_parts:
            system_parts = [
                "## Peran:",
                *system_parts
            ]

        return "\n\n".join([
            "\n".join(system_parts),
            "\n".join(history),
            "### Jawaban IT Support:"
        ])
