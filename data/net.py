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

types = {k: np.int32 for k in range(28)}
types[1] = np.string_
types[2] = np.string_

fifa = pd.read_csv("__data_set.csv", encoding='utf8', dtype=types, index_col=0, header=None)
# fifa = fifa.drop([1, 2], axis=1)
fifa.columns = range(0, len(fifa.columns))

feature = fifa.drop([24], axis=1).values
target = fifa[24].values

X_train, X_test, y_train, y_test = train_test_split(feature, target, test_size=0.2)
print(len(X_train))
print(len(X_test))
classifiers = [
    #KNeighborsClassifier(3),
    #SVC(kernel="linear", C=0.025),
    # SVC(gamma=2, C=1),
    #GaussianProcessClassifier(1.0 * RBF(1.0)),
    #DecisionTreeClassifier(),
    #RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
    #MLPClassifier(alpha=0),
    AdaBoostClassifier(),
    #GaussianNB(),
    #QuadraticDiscriminantAnalysis()
]

result = []
for i, clf in enumerate(classifiers):
    c = clf.fit(X_train, y_train)

    l = []
    for i, p in enumerate(clf.predict(X_test)):
        l.append(y_test[i] == p)
        print(p)
        print(y_test[i])
    print(l)

    score = clf.score(X_test, y_test)
    result.append('%s -> %f' % (type(c).__name__, score))

print(result)

# Einsatz 2€

# URU vs RUS 1 0 2
# SAD vs EGY 1 0 2
