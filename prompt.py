import os

class PromptBuilder:
    def __init__(self, role, article=None, chat_history=None):
        self.role = (role or '').strip()
        self.article = (article or '').strip()
        self.chat_history = chat_history or []
        
        file_path = os.path.abspath(self.role)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                self.role = f.read()

    def get_role(self, sender):
        return 'user' if sender else 'assistant'

    def get_chatml_prompt(self, article=None, chat_history=None):
        article = article or self.article
        chat_history = chat_history or self.chat_history

        messages = []

        # System message (role + article)
        content = self.role
        if article:
            content += f"\n\nArtikel:\n{article}"
        messages.append({
            'role': 'system',
            'content': content
        })

        # Chat history
        for entry in chat_history:
            messages.append({
                'role': self.get_role(entry.get('senderId')),
                'content': entry.get('message', '').strip()
            })

        return messages

    def get_qwen_prompt(self, article=None, chat_history=None):
        article = article or self.article
        chat_history = chat_history or self.chat_history

        history = [
            f"<|im_start|>{self.get_role(entry.get('senderId'))}\n{entry.get('message', '').strip()}\n<|im_end|>"
            for entry in chat_history
        ]

        system_parts = [f"<|im_start|>system\n{self.role}"]
        if article:
            system_parts.append(
                f"\n------\n\nArtikel:\n{article}"
            )
        system_parts.append("<|im_end|>")

        return '\n'.join([*system_parts, *history, "<|im_start|>assistant"])

    def get_plain_prompt(self, article=None, chat_history=None):
        article = article or self.article
        chat_history = chat_history or self.chat_history

        history = [
            f"### {entry.get('senderId')}:\n{entry.get('message', '').strip()}"
            for entry in chat_history
        ]

        parts = [f"## Peran:\n{self.role}", "------"]

        if article:
            parts.extend([f"## Artikel:\n{article}", "------"])
        joined_history = "\n\n".join(history)
        parts.append(f"## Riwayat percakapan:\n{joined_history}")
        parts.append("### Jawaban IT Support: ")

        return '\n\n'.join(parts).strip()
