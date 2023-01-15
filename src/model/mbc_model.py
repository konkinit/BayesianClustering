from numpy import array, zeros, ones, vstack, trace, exp, pi, sqrt
from pandas import DataFrame, read_csv
from os import chdir
import statsmodels.api as sm
from sklearn.cluster import KMeans
from scipy.optimize import minimize


chdir("C:/Users/idris/Desktop/ENSAE/S1_3A/Statistique_Bayesienne/BayesianStats/")


class mb_clustering:
    def __init__(self, data:DataFrame, K:int) -> None:
        self.X = data.iloc[:, 2:]
        self.y = data.iloc[:, [1]]
        self.nClusters = K
        self.Theta = zeros(K)
        self.Beta = zeros(data.shape[1])
        self.Z, self.Z_hat = zeros((data.shape[0], K)), zeros((data.shape[0], K))

    
    def initZ(self):
        """
        initialize the Z vector using the ecommeded method:
        the k-means algorithm applied to the regression residuals.
        """
        OLS_residuals = sm.OLS(self.y, sm.add_constant(self.X)).fit().resid.values
        OLS_residuals = OLS_residuals.reshape(len(OLS_residuals), 1)

        kmeans = KMeans(n_clusters=self.nClusters, random_state=42).fit(OLS_residuals)
        clustersVect = kmeans.labels_
        return vstack([(clustersVect == i).astype(int) for i in range(self.nClusters)]).T


    def tau(self):
        """
        compute the vector of tau
        """
        ZHat = self.Z_hat
        return array([ZHat[:, j].mean() for j in range(ZHat.shape[1])])


    def sigma(self): 
        """
        compute sigmaHat square
        """
        ZHat, Theta_, Beta_ = self.Z_hat, self.Theta, self.Beta
        X_, y_ = self.X, self.y
        n_, K_ = self.y.shape[0], self.nClusters
        error_matrix = array([[(y_[i] - Theta_[j] - X_[i].dot(Beta_) for j in range(K_))**2] for i in range(n_)])
        return trace(ZHat.dot(error_matrix.T)) / n_


    def Zhat(self):
        """
        compute Zhat at a given iteration
        """
        tau_, sigma_ = self.tau(), self.sigma()
        y_, X_ = self.y, self.X
        theta_, beta_ = self.Theta, self.Beta
        phi_ = lambda i, j: tau_[j] * exp(-(1/(2*sigma_**2))*(y_[i] - theta_[j] - X_[i]*beta_)**2)
        phi_normlize = lambda i: array([phi_(i, j) for j in range(self.nClusters)]).sum()
        return array([[phi_(i, j)/phi_normlize(i) for j in range(self.nCluster)] for i in range(y_.shape[0])])

    
    def Zhat_to_Z(self):
        """
        compute Z from Z_hat
        """
        ZHat = self.Z_hat
        return vstack([(ZHat[i] == ZHat.max(axis=1)[i]).astype(int) for i in range(ZHat.shape[0])])


    def weighted_ls(x, ZHat, X_, y_, K_)->float:
        """
        compute the weighted least squares function:
        x denotes the stack of vectors Theta_, Beta_ of length K+p
        """
        n_ = X_.shape[0]

        Theta_, Beta_ = x[:K_], x[K_:]
        error_matrix = array([[(y_[i] - Theta_[j] - X_[i].dot(Beta_) for j in range(K_))**2] for i in range(n_)])
        return trace(ZHat.dot(error_matrix.T))

    
    def minimizaton(self):
        """
        solve the minimizaion problem using the scipy solver
        """
        ZHat, X_, y_ = self.Z_hat, self.X, self.y
        n_, K_ = self.X.shape[0], self.nClusters
        x0 = ones(n_+K_)
        res = minimize(
                weighted_ls, 
                x0, 
                method='nelder-mead', 
                args=(ZHat, X_, y_, K_), 
                options={'xatol': 1e-8, 'disp': True}
                )
        return res.x


    def EM_algo(self, Niter):
        """
        solve the minimisation program
        """
        ZPrev, ZHatPrev = self.initZ(), self.initZ()
        for _ in range(Niter):
            self.Z_hat, self.Z = ZPrev, ZHatPrev
            stack_Theta_Beta = self.minimizaton()
            self.Theta = stack_Theta_Beta[:self.nClusters]
            self.Beta = stack_Theta_Beta[self.nClusters:]
            self.Sigma = self.sigma()
            self.Tau = self.tau()
            self.Z_hat = self.Zhat()
            self.Z = self.Zhat_to_Z()
            if self.Z == ZPrev:
                break
            else:
                ZPrev, ZHatPrev = self.Z, self.Z_hat
        return self.Tau, self.Theta, self.Beta


    def model_likelihood(self):
        """
        compute the model log-likelihood for BIC evaluation
        """
        y_, X_ = self.y, self.X
        Theta_, Beta_ = self.Theta, self.Beta
        n_, K_ = self.y.shape[0], self.nClusters
        normal_pdf = lambda x: (1/sqrt(2*pi))*exp(-(0.5)*x**2)
        likelihood = array([[(1/sqrt(self.sigma()))*normal_pdf((y_[i] - Theta_[j] - X_[i].dot(Beta_) for j in range(K_))/sqrt(self.sigma()))] for i in range(n_)])
        return likelihood.dot(self.tau()).prod()

    
    def BIC(self):
        """
        compute the model BIC evaluation
        """
        return self.model_likelihood() - (2*self.nClusters + self.X.shape[1])


data_happiness = read_csv("./data/world_data_processed.csv", sep=";")
print(mb_clustering(data_happiness, 5).initZ())