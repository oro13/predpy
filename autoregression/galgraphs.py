import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tqdm
from basis_expansions.basis_expansions import NaturalCubicSpline
from regression_tools.dftransformers import (ColumnSelector, FeatureUnion,
                                             Identity, MapFeature,
                                             StandardScaler)
from regression_tools.plotting_tools import (bootstrap_train, display_coef,
                                             plot_bootstrap_coefs,
                                             plot_partial_dependences,
                                             plot_partial_depenence,
                                             plot_univariate_smooth,
                                             predicteds_vs_actuals)
from sklearn.metrics import auc, roc_curve
from sklearn.pipeline import Pipeline
# from autoregression import autoregression

# Always make it pretty.
plt.style.use('ggplot')


def sort_features(df):
    """Takes a dataframe, returns lists of continuous and category (category) features
    INPUT: dataframe
    OUTPUT: two lists of continuous and category features"""
    continuous_features = []
    category_features = []
    for type, feature in zip(df.dtypes, df.dtypes.index):
        if type == np.dtype('int') or type == np.dtype('float'):
            continuous_features.append(feature)
        if type == np.dtype('O') or type == np.dtype('<U') or type == np.dtype('bool'):
            category_features.append(feature)
    return (continuous_features, category_features)


def emperical_distribution(x, data):
    """ Adds data and normalizes, between 0 and 1
        INPUT:
            x:
                list, array or dataframe of floats or ints
            data:
                list, array or dataframe of floats or ints
            Same length required
        OUTPUT:
            New output list between 0 and 1 of length len(x)
    """
    weight = 1.0 / len(data)
    count = np.zeros(shape=len(x))
    for datum in data:
        count = count + np.array(x >= datum)
    return weight * count


# def plot_emperical_distribution(ax, data):
#         """ plots a emperical CMF of data on the matplotib axis ax
#         INPUT:
#             ax:
#                 matplotlib axis
#                 (use 'fig, ax, subplots(1,1)')
#             data:
#                 list, array or dataframe of floats or ints
#             Same length required
#         OUTPUT:
#             A CMF plot.
#     """
#     if type(data).__name__ == 'DataFrame':
#         for column in data:
#             minimum = data[column].min()
#             maximum = data[column].max()
#             buff = (maximum - minimum) / 10
#             line = np.linspace(data[column].min() - buff,
#                             data[column].max() + buff, len(data[column]))
#             ax.plot(line, emperical_distribution(line, data[column]))
#     else:
#         minimum = min(data)
#         maximum = max(data)
#         buff = (maximum - minimum) / 10
#         line = np.linspace(minimum - buff, maximum + buff, len(data))
#         ax.plot(line, emperical_distribution(line, data))


def one_dim_scatterplot(ax, data, jitter=0.2, **options):
    """ plots a jitter plot of data on the matplotib axis ax
        INPUT:
            ax:
                matplotlib axis
                (use 'fig, ax = matplotlib.pyplot.subplots(1,1)')
            data:
                list, array or dataframe of floats or ints
            jitter:
                a float that widens the data, make this wider according to number of datapoints.
            **options:
                the **options input found in matplotlib scatter
        OUTPUT:
            A jitterplot on ax.
    """
    if jitter:
        jitter = np.random.uniform(-jitter, jitter, size=data.shape)
    else:
        jitter = np.repeat(0.0, len(data))
    ax.scatter(data, jitter, s=5, **options)
    ax.yaxis.set_ticklabels([])
    ax.set_ylim([-1, 1])

def plot_one_scatter_matrix(plot_sample_df):
    scatter_matrix = pd.plotting.scatter_matrix(
        plot_sample_df,
        figsize=((len(plot_sample_df) * .07, len(plot_sample_df) * .07)),
        marker = ".",
        alpha = .5,
        s = 50,
        diagonal = "kde"
    )
    for ax in scatter_matrix.ravel():
        ax.set_xlabel(ax.get_xlabel(), fontsize = 20, rotation = 90)
        ax.set_ylabel(ax.get_ylabel(), fontsize = 20, rotation = 0)
    return None

def plot_scatter_matrix(df, y_var_name=None):
    """ plots a series of scatter matrix of the continuous variables
        INPUT:
            df:
                dataframe
            y_var_name:
                string, the column name of the dependent y variable in the dataframe
            jitter:
                a float that widens the data, make this wider according to number of datapoints.
            **options:
                the **options input found in matplotlib scatter
        OUTPUT:
            A jitterplot on ax.
    """
    (continuous_features, category_features) = sort_features(
                                                df.drop(y_var_name, axis=1))
    if len(df) < 300:
        sample_limit = len(df)
    else:
        sample_limit = 300
    if y_var_name:
        if y_var_name in continuous_features:
            continuous_features.remove(y_var_name)
    while 5 < len(continuous_features):
        if y_var_name:
            plot_sample_df = df[[y_var_name] +
                                continuous_features[:6]].sample(n=sample_limit)
        else:
            plot_sample_df = df[continuous_features[:6]].sample(n=sample_limit)

        # pd.plotting.scatter_matrix(plot_sample_df, figsize=(len(plot_sample_df) * .07,
        #                                            len(plot_sample_df) * .07))
        plot_one_scatter_matrix(plot_sample_df)
        plt.show()
        continuous_features= continuous_features[5:]
    plot_sample_df = df[[y_var_name] + continuous_features].sample(n=sample_limit)
    plot_one_scatter_matrix(plot_sample_df)

def plot_one_univariate(ax, df, x_var_name, y_var_name, mask=None):
    """ A linear spline regression of two columns in the dataframe.
        INPUT:
            ax:
                Matplotlib axis to plot on.
                (use 'fig, ax = matplotlib.pyplot.subplots(1,1)')
            df:
                Dataframe of floats or ints.
            x_var_name:
                the column name of the x var from dataframe
            y_var_name:
                string, the column name of the dependent y variable in the dataframe
        OUTPUT:
            A linear regression, with light blue bootstrapped lines showing the instability of the regression
    """
    min_y = min(df[y_var_name])
    max_y = max(df[y_var_name])
    ax.set_ylim(min_y - .1 * np.abs(min_y), max_y + .1 * np.abs(max_y))
    if mask is None:
        plot_univariate_smooth(
            ax,
            df[x_var_name].values.reshape(-1, 1),
            df[y_var_name],
            bootstrap=200)
    else:
        plot_univariate_smooth(
            ax,
            df[x_var_name].values.reshape(-1, 1),
            df[y_var_name],
            mask=mask,
            bootstrap=200)

def plot_many_univariates(df, y_var_name):
    """ A linear spline regression all continuous columns in the dataframe. of string 'y_var' across the named string 'xvar' in the dataframe var_name on matplotlib axis 'ax'
        INPUT:
            ax:
                matplotlib axis
                (use 'fig, ax = matplotlib.pyplot.subplots(1,1)')
            dataframe:
                dataframe of floats or ints
            x_var_name:
                the column name of the x variable in the dataframe
            y_var_name:
                string, the column name of the dependent y variable in the dataframe
        OUTPUT:
            A linear regression, with light blue bootstrapped lines showing the instability of the regression
    """
    (continuous_features, category_features) = sort_features(df)
    continuous_features_greater_two = list(filter(lambda x: len(df[x].unique()) > 2, continuous_features))
    if len(continuous_features_greater_two) > 1:
        num_plot_rows=int(np.ceil(len(continuous_features_greater_two) / 2.0))
        fig, axs=plt.subplots(
            num_plot_rows, 2, figsize=(14, 3 * num_plot_rows))
        for i, continuous_feature in tqdm.tqdm(enumerate(continuous_features_greater_two)):
            # if len(df[continuous_feature].unique()) > 2:
            plot_one_univariate(
                axs.flatten()[i], df, continuous_feature, y_var_name)
            axs.flatten()[i].set_title(
                f"{continuous_feature}: Univariate Plot")
    elif len(continuous_features_greater_two) == 1:
        fig, axs=plt.subplots(len(continuous_features_greater_two), 1, figsize=(
            14, 4.5 * len(continuous_features_greater_two)))
        for i, continuous_feature in enumerate(continuous_features_greater_two):
            plot_one_univariate(axs, df, continuous_feature, y_var_name)
            axs.set_title("{}: Univariate Plot".format(continuous_feature))
            fig.set_tight_layout(tight=True)  # this doesn't work!!!
            # 'tight_layout' must be used in calling script as well
            fig.tight_layout(pad=2)
    else:
        print('No Continous Features to Plot')

def plot_predicted_vs_actuals(df, model, y_var_name, sample_limit):
    """ Plots all the y_var_name predictions from the model in the dataframe 'df' vs the actual data in column y_var_name
        INPUT:
            dataframe:
                dataframe of floats or invts
            model:
                A sklearn model with a predict method
                Call fit() on model before using plot_feature_importances.
            y_var_name:
                string, the column name of the dependent y variable in the dataframe
            y_hat:
                a array of y values you predicted to be compared with the values of y_var_name
        OUTPUT:
            Plot of predicted data (in red) against actual data (in grey)
    """
    X=df.drop(y_var_name, axis=1).values
    name=model.__class__.__name__
    plot_sample_df=df.sample(sample_limit)
    fig, ax=plt.subplots(figsize=(12, 4))
    ax.set_title(name + " Predicteds vs Actuals at " + \
                 df.drop(y_var_name, axis=1).columns[0])
    ax.scatter(df[df.drop(y_var_name, axis=1).columns[0]],
               df[y_var_name], color="grey", alpha=0.5)
    ax.scatter(df[df.drop(y_var_name, axis=1).columns[0]], model.predict(X))

def plot_many_predicteds_vs_actuals(df_X, x_var_names, df_y, y_hat, n_bins=50):
    """ Plots all the y predictions 'y_hat' vs the result data in the dataframe in column y_var_name
        INPUT:
            dataframe:
                dataframe of floats or invts
            x_var_names:
                a list of strings that are columns of dataframe
            y_var_name:
                string, the column name of the dependent y variable in the dataframe
            y_hat:
                a array of y values you predicted to be compared with the values of y_var_name
        OUTPUT:
            Plot of estimated data (in red) against total data (in grey)
    """
    num_plot_rows=int(np.ceil(len(x_var_names) / 2.0))
    fig, axs=plt.subplots(num_plot_rows, 2, figsize=(12, 3 * num_plot_rows))
    for ax, name in zip(axs.flatten(), x_var_names):
        x=df_X[name]
        predicteds_vs_actuals(ax, x, df_y, y_hat)
        ax.set_title("{} Predicteds vs. Actuals".format(name))
    return fig, axs

def plot_coefs(coefs, columns, graph_name):

    fig, ax=plt.subplots(1, 1, figsize=(13, len(coefs) * 0.3))
    y_pos=np.arange(len(coefs))
    ax.barh(np.arange(len(coefs)), coefs, tick_label=columns)
    plt.ylim(min(y_pos) - 1, max(y_pos) + 1)
    ax.set_title('Standardized Coefficents of ' + graph_name)

def plot_feature_importances(model, df_X):
    """Plots the feature importances in fit models
    Warning: Avoid comparing continuous and non-continuous features.
    Feature importance is proporational to number of possible splits.
    INPUT:
        model:
            A fit sklean object with a `coef_` attribute.
            Call fit() on model before using plot_feature_importances.
        df_X:
            dataframe of floats, the independent variables.
            must have same features to the df_X's put into the model.
    OUTPUT:
        A plot showing the feature importances of the model.
    """
    if 'feature_importances_' in dir(model):
        feat_scores = pd.DataFrame({'Fraction of Samples Affected': model.feature_importances_},
                               index=df_X.columns)
        feat_scores = feat_scores.sort_values(by='Fraction of Samples Affected')
        feat_scores.plot(kind='barh', figsize=(10,len(feat_scores) * 0.3))
    else:
        raise ValueError(f"Model: {model} doesn't have feature_importances_, unable to plot")
    return None

def plot_residual(ax, x, y, y_hat, n_bins=50, s=3):
    """ Plots all the residuals from y and 'y_hat' across x
        INPUT:
            dataframe:
                dataframe of floats or invts
            x:
                a dataframe,list or array of ints or floats
            y
                a dataframe,list or array of ints or floats
            y_hat:
                a array of y values you predicted from x to be compared with the values of y
        OUTPUT:
            A plot showing the residuals across x (error)
    """
    residuals=np.abs(y.astype(int) - y_hat)
    ax.axhline(0, color="black", linestyle="--")
    ax.scatter(x, residuals, color="grey", alpha=0.5, s=s)
    ax.set_ylabel("Residuals ($y - \hat y$)")

def plot_residual_error(ax, x, y, y_hat, n_bins=50, alpha=.7, s=2):
    """ Plots all the residuals from y and 'y_hat' across x
        INPUT:
            dataframe:
                dataframe of floats or invts
            x:
                a dataframe,list or array of ints or floats
            y
                a dataframe,list or array of ints or floats
            y_hat:
                a array of y values you predicted from x to be compared with the values of y
        OUTPUT:
            A plot showing the residuals across x (error)
    """
    residuals=y - y_hat
    ax.axhline(0, color="black", linestyle="--")
    ax.scatter(x, residuals, color="red", alpha=alpha, s=s)
    ax.set_ylabel("Residuals ($y - \hat y$)")

def plot_many_residuals(df_X, y, y_hat, n_bins=50):
    """ Plots all the y predictions 'y_hat' vs the result data in the dataframe in column y_var_name
        INPUT:
            df_X:
                dataframe of floats, the independent variables.
            x_var_names:
                a list of strings that are columns of dataframe
            y_var_name:
                # the column name of the dependent y variable from dataframe
            y_hat:
                a array of y values you predicted to be compared with the values of y_var_name
        OUTPUT:
            A series of plots showing the residuals across x (error)
    """
    fig, axs=plt.subplots(len(df_X), figsize=(12, 3 * len(df_X)))
    for ax, name in tqdm.tqdm(zip(axs, df_X)):
        plot_residual(ax, df_X[name], y, y_hat)
        ax.set_xlabel(name)
        ax.set_title("Model Residuals by {}".format(name))
    return fig, axs

def simple_spline_specification(name, knots=10):
    """Make a pipeline taking feature (aka column) 'name' and outputting n-2 new spline features
        INPUT:
            name:
                string, a feature name to spline
            knots:
                int, number knots (divisions) which are divisions between splines.
        OUTPUT:
            pipeline returning of n-2 new splines after transformed
    """
    select_name="{}_select".format(name)
    spline_name="{}_spline".format(name)
    return Pipeline([
        (select_name, ColumnSelector(name=name)),
        (spline_name, NaturalCubicSpline(knots=knots))
    ])

def standardize_y(y_train, y_test):
    """standardize both variables such that each has a mean of 0 and std of 1.
        INPUT:
            y_train:
                array of floats or ints
            y_test:
                array of floats or ints
        OUTPUT:
            the new y_train and y_test_std, which has a mean of 0 and std of 1.
    """
    y_mean, y_std=np.mean(y_train), np.std(y_train)
    y_train_std=(y_train - y_mean) / y_std
    y_test_std=(y_test - y_mean) / y_std
    return y_train_std, y_test_std, y_mean, y_std

def plot_solution_paths(ax, regressions):
    """Standardize both variables such that each has a mean of 0 and std of 1.
        INPUT:
            ax:
                plot_solution_paths plots on this axis
            regressions:
                a list of arrays to see the space.
                for example:
                    >>> ridge_regularization_strengths = np.logspace(np.log10(0.000001), np.log10(10000), num=100)
                    >>> ridge_regressions = []
                    for alpha in ridge_regularization_strengths:
                        ridge = Ridge(alpha=alpha)
                        ridge.fit(balance_train, y_train)
                        ridge_regressions.append(ridge)
        OUTPUT:
            the new y_train and y_test_std, which has a mean of 0 and std of 1.
    """
    alphas=[np.log10(ridge.alpha) for ridge in regressions]
    coeffs=np.concatenate([ridge.coef_.reshape(1, -1)
                             for ridge in regressions])
    for idx in range(coeffs.shape[1]):
        ax.plot(alphas, coeffs[:, idx])
    ax.set_xlabel(r"$\log_{10}(\alpha)$")
    ax.set_ylabel("Estimated Coefficient")
    ax.set_title("Coefficient Paths")

def gal_display_coef(coefs, coef_names):
    """Pretty print a table of the parameter estimates in a linear model.

    Parameters
    ----------
    coeffs:
        suggested from a model.fit() sklearn object with a `coef_` attribute.

    coef_names: A list of names associated with the coefficients.
    """
    print("{:<35}{:<20}".format("Name", "Parameter Estimate"))
    print("-" * (35 + 20))
    for coef, name in zip(coefs, coef_names):
        row="{:<35}{:<20}".format(name, coef)
        print(row)

def shaped_plot_partial_dependences(model, df, y_var_name, pipeline=None,
                                    n_points=250, **kwargs):
    """Creates many partial dependency plots.
        INPUT:
            model:
                A sklearn model
                Call fit() on model before using plot_feature_importances.
            df:
                A dataframe containing independent variables y
                and dependent variables X.
            y_var_name:
                String, the column name of the dependent y variable in the dataframe
            pipeline:
                Runs on df_X (without y), already fit to df_X.
            n_points:
                the number of points to plot
            *kwargs:
                extra arguments passed to plot_partial_dependence
        OUTPUT:
            an array of partial dependence plots, describing each varible's contibution to the regression.
    """

    X_features=list(df.columns)
    X_features.remove(y_var_name)
    if len(X_features) > 1:
        num_plot_rows=int(np.ceil(len(X_features) / 2.0))
        fig, axs=plt.subplots(
            num_plot_rows, 2, figsize=(14, 3 * num_plot_rows))
        for i, X_feature in enumerate(X_features):
            # print(model)
            plot_partial_depenence(axs.flatten()[i],
                                   model=model,
                                   X=df.drop(y_var_name, axis=1),
                                   var_name=X_feature,
                                   y=df[y_var_name],
                                   pipeline=pipeline,
                                   n_points=n_points,
                                   **kwargs)
            axs.flatten()[i].set_title("{}: Partial Dependence Plot {}".format(X_feature,
                                                                  model.__class__.__name__))
    elif len(X_features) == 1:
        fig, axs=plt.subplots(len(X_features), 1,
                              figsize=(14, 4.5 * len(X_features)))
        for i, X_feature in enumerate(X_features):
            plot_partial_depenence(axs,
                                   model=model,
                                   X=df.drop(y_var_name, axis=1),
                                   var_name=X_feature,
                                   y=df[y_var_name],
                                   pipeline=pipeline,
                                   n_points=n_points,
                                   **kwargs)
            axs.set_title("{}: Partial Dependence Plots {}".format(X_feature,
                                                                  model.__class__.__name__))
            fig.set_title("Partial Dependence Plots for " + \
                          model.__class__.__name__)
#             fig.set_tight_layout(tight = True) #this doesn't work!!!
            # 'tight_layout' must be used in calling script as well
        fig.tight_layout(pad=2)
    else:
        print('No Features to Plot')

def plot_partial_dependences(model, X, var_names, y=None, bootstrap_models=None, pipeline=None, n_points=250):
    """Creates many partial dependency plots.
        INPUT:
            model:
                A sklearn model
                Call fit() on model before using plot_feature_importances.
            X:
                A dataframe or array containing independent variables
                that fit in pipeline.
            var_names:
                The column names of the x variables in the
                dataframe you want plotted.
            y:
                A dataframe or array, the dependent variable.
                Plotted in grey.
            pipeline:
                Runs on df_X (without y), already fit to df_X.
            n_points:
                The number of points to plot.
            *kwargs:
                Extra arguments passed to plot_partial_dependence.
        OUTPUT:
            an array of partial dependence plots, describing each varible's
            contibution to the regression.
    """
    fig, axs=plt.subplots(len(var_names), figsize=(12, 3 * len(var_names)))
    for ax, name in zip(axs, var_names):
        if bootstrap_models:
            for M in bootstrap_models[:10]:
                # print(M)
                plot_partial_depenence(
                    ax, M, X=X, var_name=name, pipeline=pipeline, alpha=0.8,
                    linewidth=1, color="lightblue")
        # print(model)
        plot_partial_depenence(ax, model, X=X, var_name=name,
                               y=y, pipeline=pipeline, color="blue", linewidth=3)
        ax.set_title("{} Partial Dependence".format(name))
    fig.tight_layout()
    return fig, axs

def plot_roc(ax, model, df_X, y, pipeline=None):
    """ plot the fpr and tpr for all thresholds of the classification
        INPUT:
            ax:
                plot_solution_paths plots on this axis
            model:
                A sklearn model witha predict method
                Call fit() on model before using plot_feature_importances.
            df_X:
                dataframe of floats, the independent variables.
            y:
                A dataframe or array. Must be equal in rows to df_X Must be True/False's or 1/0's.
                The dependent variable. Is plotted in grey.
            pipeline:
                runs on df_X (without y), already fit to df_X.
        OUTPUT:
            a ROC plot, used to compare binary classifiers
    """
    if pipeline:
        probs=model.predict_proba(pipeline.transform(df_X))
    else:
        probs=model.predict_proba(df_X)
    preds=probs[:, 1]
    fpr, tpr, threshold=roc_curve(y, preds)
    roc_auc=auc(fpr, tpr)
    ax.set_title('Receiver Operating Characteristic')
    ax.plot(
        fpr, tpr, label=f'AUC {model.__class__.__name__} = %0.2f' % roc_auc)
    ax.legend(loc='lower right', fontsize=20)
    ax.plot([0, 1], [0, 1], 'r--')
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    ax.set_ylabel('True Positive Rate')
    ax.set_xlabel('False Positive Rate')

def plot_rocs(models, df_X, y, pipeline=None):
    """ plot the fpr and tpr for all thresholds of the classification
        INPUT:
            models:
                a list of pre-fit models with a predict method
            df_X:
                dataframe of floats, the independent variables.
            y:
                A dataframe or array. Must be equal in rows to df_X Must be True/False's or 1/0's.
                The dependent variable. Is plotted in grey.
            pipeline:
                runs on df_X (without y), already fit to df_X.
        OUTPUT:
            a ROC plot, used to compare binary classifiers
    """
    if pipeline:
        df_X=pipeline.transform(df_X)
    fig, ax=plt.subplots(1, 1, figsize=(10, 10))

    for model in models:
        # pipeline intentionally tranformed before inserting df_X, pipeline should not be passed!
        if 'predict_proba' in dir(model):
            plot_roc(ax, model, df_X, y, pipeline=None)
        # one day use on RidgeCV:
        # d = clf.decision_function(x)[0]
        # probs = np.exp(d) / np.sum(np.exp(d))
    return None


def plot_box_and_violins(names, scoring, results):
    """ Plots two violin plots and box plots for comparison.
        INPUT:
            names:
                a list of regression names, plotted in axis
            scoring:
                string describing scoring method, plotted in title
            results:
                a list of arrays containing CV scores
    """
    fig, ax = plt.subplots(2, 2, figsize=(20, 20))
    ax = ax.flatten()
    fig.suptitle(f'Model Crossval Scores: {scoring}')

    # BOX PLOTS
    ax[0].boxplot(results, vert=True)
    ax[0].set_xticks(list(range(len(names)+1)))
    ax[0].set_xticklabels([''] + names)
    ax[0].set_ylabel(f'{scoring}')

    # VIOLIN PLOTS
    ax[1].violinplot(results, vert=True)
    ax[1].set_xticks(list(range(len(names)+1)))
    ax[1].set_xticklabels([''] + names)

    # BOX PLOTS OF LOG(ERROR)
    ax[2].boxplot(results, vert=True)
    ax[2].set_xticks(list(range(len(names)+1)))
    ax[2].set_xticklabels(['']+names)
    ax[2].set_ylabel(f'{scoring}')
    ax[2].set_yscale('log')
    ax[2].get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

    # VIOLIN PLOTS OF LOG(ERROR)
    ax[3].violinplot(results, vert=True)
    ax[3].set_xticks(list(range(len(names)+1)))
    ax[3].set_xticklabels(['']+names)
    ax[3].set_yscale('log')
    ax[3].get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
