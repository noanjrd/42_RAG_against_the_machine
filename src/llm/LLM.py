"""Wrapper around the Qwen model (tokenizing and answering)."""
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Any


class LLM:
    """Qwen3-0.6B tokenizer and causal language model.
    """
    def __init__(self) -> None:
        """Load the tokenizer and the model from Hugging Face.

        Returns:
            None.
        """
        self.model_name = "Qwen/Qwen3-0.6B"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.answerer: Any = AutoModelForCausalLM.from_pretrained(
            self.model_name, dtype=torch.float32)

        return

    def tokenize(self, text: str) -> list[str]:
        """Split a text into tokens.

        Args:
            text: Text to tokenize.

        Returns:
            The tokens.
        """
        tokenized: list[str] = self.tokenizer.tokenize(text)
        return tokenized

    def answer(self, prompt: str) -> str:
        """Generate an answer from a prompt (at most 75 new tokens).

        The model is told to answer only from the documentation in the prompt.

        Args:
            prompt: Prompt containing the documentation and the question.

        Returns:
            The generated answer.
        """
        messages = [{"role": "system",
                     "content": "You answer questions using only the "
                     "provided documentation. "
                     "If the answer isn't there, say you don't know."},
                    {"role": "user",
                     "content": prompt}]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False)
        encoded_prompt = self.tokenizer(text, return_tensors="pt")
        encoded_prompt_len = encoded_prompt["input_ids"].shape[1]
        output = self.answerer.generate(**encoded_prompt, max_new_tokens=75)
        output = output[0][encoded_prompt_len:]
        answer = str(self.tokenizer.decode(output, skip_special_tokens=True))
        return answer
