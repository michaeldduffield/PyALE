import  numpy as np
from statsmodels.distributions.empirical_distribution import ECDF

def cmds(D, k=2):
    """
    https://en.wikipedia.org/wiki/Multidimensional_scaling#Classical_multidimensional_scaling
    http://www.nervouscomputer.com/hfs/cmdscale-in-python/
    """
    # Number of points                                                                        
    n = len(D)
    if k > (n-1):
        raise Exception('k should be an integer <= len(D) - 1' )
    # (1) Set up the squared proximity matrix
    D_double = D**2
    # (2) Apply double centering: using the centering matrix
    # centering matrix
    center_mat = np.eye(n) - np.ones((n, n))/n
    # apply the centering
    B = -(1/2) * center_mat.dot(D_double).dot(center_mat)
    # (3) Determine the m largest eigenvalues 
    # (where m is the number of dimensions desired for the output)
    # extract the eigenvalues
    eigenvals, eigenvecs = np.linalg.eigh(B)
    # sort descending
    idx = np.argsort(eigenvals)[::-1]
    eigenvals = eigenvals[idx]
    eigenvecs = eigenvecs[:, idx]
    # (4) Now, X=eigenvecs.dot(eigen_sqrt_diag), where eigen_sqrt_diag = diag(sqrt(eigenvals))
    eigen_sqrt_diag = np.diag(np.sqrt(eigenvals[0:k]))
    ret = eigenvecs[:,0:k].dot(eigen_sqrt_diag)
    return(ret)


def order_groups(X, feature):
    """
    Assign an order to the values of the feature based on a distance matrix between
    the other variables/features in X
    """
    features = X.columns
    groups = X[feature].cat.categories.values
    D_cumu = pd.DataFrame(0, index=groups, columns=groups)
    K = len(groups)
    for j in set(features) - set([feature]):
        D = pd.DataFrame(index=groups, columns=groups)
        # discrete/factor feature j
        # e.g. j = 'color'
        if (X[j].dtypes.name == 'category') | ((len(X[j].unique()) <= 10) & ('float' not in X[j].dtypes.name)):
            # counts and proportions of each value in j in each group in 'feature' 
            cross_counts = pd.crosstab(X[feature], X[j])
            cross_props = cross_counts.div(np.sum(cross_counts, axis=1), axis=0)
            for i  in range(K):
                group = groups[i]
                D_values = abs(cross_props - cross_props.loc[group]).sum(axis=1)/2
                D.loc[group, :] = D_values
                D.loc[:, group] = D_values
        else:
            # continuous feature j
            # e.g. j = 'carat'
            # extract the 1/100 quantiles of the feature j
            seq = np.arange(0, 1, 1/100)
            q_X_j = X[j].quantile(seq).to_list()
            # get the ecdf (empiricial cumulative distribution function)
            # compute the function from the data points in each group
            X_ecdf = X.groupby(feature)[j].agg(ECDF)
            # apply each of the functions on the quantiles
            # i.e. for each quantile value get the probability that j will take a value less than 
            # or equal to this value.
            q_ecdf = pd.DataFrame()
            q_ecdf = X_ecdf.apply(lambda x : x(q_X_j))
            for i in range(K):
                group = groups[i]
                D_values = abs(q_ecdf - q_ecdf[group]).apply(max)
                D.loc[group, :] = D_values
                D.loc[:, group] = D_values
        D_cumu = D_cumu + D
    # reduce the dimension of the cumulative distance matrix to 1
    D1D = cmds(D_cumu, 1).flatten()
    # order groups based on the values
    order_idx = D1D.argsort()
    groups_ordered = D_cumu.index[D1D.argsort()]
    return(pd.Series(range(K), index=groups_ordered))
