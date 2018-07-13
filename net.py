import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import make_moons, make_circles, make_classification
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.preprocessing import StandardScaler

types = {k: np.int32 for k in range(24)}
types[0] = np.float64

# fifa = pd.read_csv('/Users/thildebrandt/Projects/FH-Wedel/Applied Data Science/data/data_simple_train.csv')
print('Read CSV...')
fifa = pd.read_csv('./data/data_simple_train.csv', dtype=types, header=None)
print('done.')
# fifa = pd.read_csv('./data/data_simple_test.csv', encoding='utf8', dtype=types, index_col=0, header=None)
# fifa = fifa.drop([1, 2], axis=1)

fifa.columns = range(0, len(fifa.columns))
print('Prepare Dataset...')
target = fifa[23].values
feature = fifa.drop([23], axis=1).values
feature = [[float(e) if k == 0 else int(e) for k, e in enumerate(f)] for f in feature]

types = {k: np.int32 for k in range(24)}
types[0] = np.float64
types[23] = np.string_
quarterfinals = pd.read_csv('./data/data_simple_test.csv', dtype=types, header=None)
quarterfinals = quarterfinals.drop([23], axis=1).values
quarterfinals = [[float(e) if k == 0 else int(e) for k, e in enumerate(f)] for f in quarterfinals]

X_train, X_test, y_train, y_test = train_test_split(feature, target, test_size=0.2)

# scaler = StandardScaler()
# # Don't cheat - fit only on training data
# scaler.fit(X_train)
# X_train = scaler.transform(X_train)
# # apply same transformation to test data
# X_test = scaler.transform(X_test)

# print(len(X_train))
# print(len(X_test))
classifiers = [
    # KNeighborsClassifier(3),
    # GaussianProcessClassifier(1.0 * RBF(1.0)),
    # SVC(kernel="linear", C=0.025),
    # SVC(gamma=2, C=1),
    # DecisionTreeClassifier(),
    RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
    # MLPClassifier(alpha=1),
    AdaBoostClassifier(),
    GaussianNB(),
    QuadraticDiscriminantAnalysis()
]

result = []
print('done.')

for i, clf in enumerate(classifiers):
    print('Train net...')
    c = clf.fit(X_train, y_train)
    print('done.')

    print('Test Dataset...')
    score = c.score(X_test, y_test)
    print('done.')

    print('Predict Quarterfinals...')
    c = clf.fit(feature, target)

    # for qf in quarterfinals:
    #     print(qf)
    prediction = clf.predict(quarterfinals)
    print(prediction)
    print('done.')

    result.append('%s -> %f' % (type(c).__name__, score))

print(result)

# Einsatz 2€

# URU vs RUS 1 0 2
# SAD vs EGY 1 0 2
