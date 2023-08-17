# Import necessary libraries
from sklearn.feature_extraction import FeatureHasher
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from keras.datasets import imdb
import numpy as np
import pandas as pd

# Load the IMDB dataset
(train_data, train_labels), (test_data, test_labels) = imdb.load_data(num_words=10000)

# Reverse from integers to words using the dictionary provided by imdb
word_index = imdb.get_word_index()
reverse_word_index = dict([(value, key) for (key, value) in word_index.items()])

def decode_review(text):
    return ' '.join([reverse_word_index.get(i, '?') for i in text]).split() # Add .split()

# Apply the decode function to the first review in the dataset
decoded_reviews = [decode_review(review) for review in train_data]

# Instantiate FeatureHasher with a predetermined size
hasher = FeatureHasher(n_features=1000, input_type='string')

# Apply the hashing trick
hashed_features = hasher.transform(decoded_reviews)

# Split the data into training and validation sets
x_train, x_val, y_train, y_val = train_test_split(hashed_features, train_labels, test_size=0.2, random_state=42)

# Train a classifier
classifier = SGDClassifier()
classifier.fit(x_train, y_train)

# Validate the classifier
print("Validation accuracy: ", classifier.score(x_val, y_val))
