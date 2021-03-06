import nltk
from nltk.tokenize import MWETokenizer
from collections import Counter
import tqdm

from typing import List, Union

class WordTokenizer:
    
    def __init__(self, 
                vocab_file=None, 
                bos_token='<BOS>', 
                eos_token='<EOS>',
                unk_token='<UNK>',
                pad_token='<PAD>',
                lower_case=True):

        self.lower_case = lower_case
        self.vocab = None
        self.rev_vocab = None
        self.vocab_file = vocab_file
        self._read_vocab()
        self._rev_vocab()
        self.bos_token = bos_token
        self.eos_token = eos_token
        self.unk_token = unk_token
        self.pad_token = pad_token
        self.mwe_tokenizer = MWETokenizer([ ('<', 'BOS', '>'),
                                            ('<', 'EOS', '>'),
                                            ('<', 'UNK', '>'),
                                            ('<', 'PAD', '>')], separator='')

    def _write_vocab(self, file_name: str) -> None:
        write_file = open(file_name, 'w', encoding='utf-8')
        for num, word in enumerate(self.vocab):
            write_file.write('{}\t{}\n'.format(num, word))
        write_file.close()

    def _read_vocab(self) -> None:
        if self.vocab_file is None:
            print('Cannot read vocab from file. You have to build it')
        else:
            with open(self.vocab_file, 'r', encoding='utf-8') as read_file:
                self.vocab = []
                for d in read_file:
                    d = d.split('\t')
                    d[0] = int(d[0])
                    d[1] = d[1].replace('\n', '')
                    self.vocab.append(d[1])
            print('Read vocab file with {} tokens'.format(len(self.vocab)))
  
    def build_vocab(self, 
                    raw_text: List[str], 
                    vocab_path='vocab.txt', 
                    threshold=0.7, 
                    return_freq=False) -> Union[None, List[tuple]]:
        vocab_ = []
        for sent in tqdm.tqdm(raw_text):
            if self.lower_case:
                sent = sent.lower()
            tokenized = nltk.word_tokenize(sent)
            tokenized = self.mwe_tokenizer.tokenize(tokenized)
            vocab_.extend(tokenized)
        cnt = Counter(vocab_)
        most_common_words_ = cnt.most_common(int(len(cnt) * threshold))
        most_common_words = [w[0] for w in most_common_words_]
        most_common_words.remove('unk')
        most_common_words.remove('<')
        most_common_words.remove('>')
        vocab = []
        if self.bos_token is not None:
            vocab.append(self.bos_token)
        if self.eos_token is not None:
            vocab.append(self.eos_token)
        if self.unk_token is not None:
            vocab.append(self.unk_token)
        if self.pad_token is not None:
            vocab.append(self.pad_token)

        vocab.extend(most_common_words)
        self.vocab = vocab
        self._write_vocab(vocab_path)
        print('Build vocab with {} tokens'.format(len(self.vocab)))
        self._rev_vocab()

        if return_freq:
            return most_common_words_
        else:
            return None

    def _rev_vocab(self) -> None:
        if self.vocab is None:
            print('Cannot build reverse vocab without vocab')
        else:
            self.rev_vocab = {token: num for num, token in enumerate(self.vocab)}

    def tokenize(self, raw_text: str) -> List[str]:
        if self.vocab is None:
            raise Exception('You cannot tokenize without vocab')
        else:
            if self.lower_case:
                raw_text = raw_text.lower()
            tokens = nltk.word_tokenize(raw_text)
            tokens = self.mwe_tokenizer.tokenize(tokens)
            for i in range(len(tokens)):
                if tokens[i] not in self.rev_vocab:
                    tokens[i] = self.unk_token

            return tokens
      
    def tokenize_batch(self, batch: List[str]) -> List[List[str]]:
        tokenized = [self.tokenize(sent) for sent in batch]
        return tokenized

    def encode(self,  tokenized_str: List[str]) -> List[int]:
        encoded = [self.rev_vocab[token] for token in tokenized_str]
        return encoded

    def encode_batch(self, tokenized_batch: List[List[str]]) -> List[List[int]]:
        encoded_batch = [self.encode(tokens) for tokens in tokenized_batch]
        return encoded_batch

    def decode(self, encoded_str: List[int]) -> List[str]:
        decoded = [self.vocab[token] for token in encoded_str]
        return decoded

    def decode_batch(self, encoded_batch: List[List[int]]) -> List[List[str]]:
        decoded_batch = [self.decode(tokens) for tokens in encoded_batch]
        return decoded_batch
