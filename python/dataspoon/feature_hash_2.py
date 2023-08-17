# Import necessary libraries
from keras.models import Sequential
from keras.layers import Dense, Embedding, LSTM
from keras.datasets import imdb
import numpy as np

# Load the IMDB dataset
top_words = 10000
(train_data, train_labels), (test_data, test_labels) = imdb.load_data(num_words=top_words)

# Define maximum review length
max_review_length = 500

# Preprocessing: Truncate and pad the sequences manually
def preprocess_data(data):
    processed_data = []
    for sequence in data:
        if len(sequence) > max_review_length:
            processed_data.append(sequence[:max_review_length])
        else:
            processed_data.append(sequence + [0]*(max_review_length - len(sequence)))
    return np.array(processed_data)

train_data = preprocess_data(train_data)
test_data = preprocess_data(test_data)

# Build LSTM model
embedding_vector_length = 32

model = Sequential()
model.add(Embedding(top_words, embedding_vector_length, input_length=max_review_length))
model.add(LSTM(100))
model.add(Dense(1, activation='sigmoid'))

# Compile the model
model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

# Train the model
model.fit(train_data, train_labels, validation_data=(test_data, test_labels), epochs=3, batch_size=64)

# Evaluate the model
scores = model.evaluate(test_data, test_labels, verbose=0)
print("Test accuracy: ", scores[1])
