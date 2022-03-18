import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def plot_subclusters(loom,
                     layername,
                     cluster,
                     sublayers=1,
                     plot_output=None,
                     label_clusters=True,
                     complexity_cutoff=0,
                     downsample_to=500,
                     blacklist=[]):
    """

    Parameters
    ----------
    loom :
        param layername:
    cluster :
        type cluster: Cluster, or list of clusters
    sublayers :
        Default value = 1)
    plot_output :
        Default value = None)
    label_clusters :
        Default value = True)
    complexity_cutoff :
        Default value = 0)
    downsample_to :
        Default value = 500)
    blacklist :
        Default value = [])
    layername :
        

    Returns
    -------

    
    """
    from panopticon.analysis import get_cluster_embedding
    import matplotlib.pyplot as plt
    if type(cluster) == str or type(cluster) == int:
        current_layer = len(str(cluster).split('-')) - 1
        supermask = (loom.ca['ClusteringIteration{}'.format(current_layer)]
                     == cluster) & (loom.ca['nGene'] >= complexity_cutoff)
    elif type(cluster) == list or type(cluster) == np.ndarray:
        current_layer_options = [len(str(x).split('-')) - 1 for x in cluster]
        if len(np.unique(current_layer_options)) != 1:
            raise Exception("All clusters of interest must be from same layer")
        else:
            current_layer = np.unique(current_layer_options)[0]
        supermask = np.isin(
            loom.ca['ClusteringIteration{}'.format(current_layer)],
            cluster) & (loom.ca['nGene'] >= complexity_cutoff)
    print(np.sum(supermask))
    keep_probability = np.min([1, downsample_to / np.sum(supermask)])
    supermask *= np.random.choice([False, True],
                                  size=len(supermask),
                                  p=[1 - keep_probability, keep_probability])
    # I kinda hate this (30 Apr 2020 smarkson)
    embedding = get_cluster_embedding(loom, layername, cluster, mask=supermask)
    if type(cluster) == str or type(cluster) == int:
        subclusters = [
            x for x in np.unique(loom.ca['ClusteringIteration{}'.format(
                current_layer + sublayers)])
            if str(x).startswith(str(cluster) + '-') and (x not in blacklist)
        ]
    elif (type(cluster) == list) or (type(cluster) == np.ndarray):
        subclusters = []
        for cluster_part in cluster:
            subclusters += [
                x for x in np.unique(loom.ca['ClusteringIteration{}'.format(
                    current_layer + sublayers)])
                if str(x).startswith(str(cluster_part) +
                                     '-') and (x not in blacklist)
            ]
    for subcluster in subclusters:
        mask = loom.ca['ClusteringIteration{}'.format(
            current_layer + sublayers)][supermask.nonzero()[0]] == subcluster
        plt.scatter(embedding[mask, 0], embedding[mask, 1], label=subcluster)
        if label_clusters:
            plt.annotate(
                subcluster,
                (np.mean(embedding[mask, 0]), np.mean(embedding[mask, 1])))
    plt.legend(ncol=len(subclusters) // 14 + 1, bbox_to_anchor=(1.05, 0.95))
    if plot_output is not None:
        plt.savefig(plot_output, bbox_inches='tight')
    else:
        plt.show()
    return embedding


def plot_cluster_umap(loom,
                      layername,
                      cluster,
                      mask=None,
                      plot_output=None,
                      label_clusters=True,
                      complexity_cutoff=0,
                      downsample_to=500,
                      blacklist=[]):
    """

    Parameters
    ----------
    loom :
        param layername:
    cluster :
        type cluster: Cluster, or list of clusters
    sublayers :
        Default value = 1)
    plot_output :
        Default value = None)
    label_clusters :
        Default value = True)
    complexity_cutoff :
        Default value = 0)
    mask :
        Default value = None)
    downsample_to :
        Default value = 500)
    blacklist :
        Default value = [])
    layername :
        

    Returns
    -------

    
    """
    from panopticon.analysis import get_cluster_embedding
    import matplotlib.pyplot as plt
    if mask is not None:
        supermask = mask
    elif type(cluster) == str or type(cluster) == int:
        current_layer = len(str(cluster).split('-')) - 1
        supermask = (loom.ca['ClusteringIteration{}'.format(current_layer)]
                     == cluster) & (loom.ca['nGene'] >= complexity_cutoff)
    elif type(cluster) == list or type(cluster) == np.ndarray:
        current_layer_options = [len(str(x).split('-')) - 1 for x in cluster]
        if len(np.unique(current_layer_options)) != 1:
            raise Exception("All clusters of interest must be from same layer")
        else:
            current_layer = np.unique(current_layer_options)[0]
        supermask = np.isin(
            loom.ca['ClusteringIteration{}'.format(current_layer)],
            cluster) & (loom.ca['nGene'] >= complexity_cutoff)
    print(np.sum(supermask))
    keep_probability = np.min([1, downsample_to / np.sum(supermask)])
    supermask *= np.random.choice([False, True],
                                  size=len(supermask),
                                  p=[1 - keep_probability, keep_probability])
    # I kinda hate this (30 Apr 2020 smarkson)
    embedding = get_cluster_embedding(loom, layername, cluster, mask=supermask)
    if plot_output is not None:
        plt.savefig(plot_output, bbox_inches='tight')
    else:
        plt.show()
    return embedding


def get_cluster_differential_expression_heatmap(loom,
                                                layer,
                                                clusteringlevel,
                                                diffex={},
                                                output=None,
                                                bracketwidth=3.5,
                                                ff_offset=0,
                                                ff_scale=7,
                                                bracket_width=3.5):
    """

    Parameters
    ----------
    loom :
        param layer:
    clusteringlevel :
        param diffex: (Default value = {})
    output :
        Default value = None)
    bracketwidth :
        Default value = 3.5)
    ff_offset :
        Default value = 0)
    ff_scale :
        Default value = 7)
    bracket_width :
        Default value = 3.5)
    layer :
        
    diffex :
        (Default value = {})

    Returns
    -------

    
    """
    from panopticon.analysis import get_cluster_differential_expression
    import seaborn as sns
    import pandas as pd

    clusteredmask = []
    for cluster in np.unique(loom.ca[clusteringlevel]):
        mask = loom.ca[clusteringlevel] == cluster
        if mask.sum() > 2:
            clusteredmask.append(np.where(mask)[0])
    clusteredmask = np.hstack(clusteredmask)
    allgenes = []
    rawX = []
    clusters = np.unique(loom.ca[clusteringlevel])
    for cluster in clusters:
        mask = loom.ca[clusteringlevel] == cluster
        if mask.sum() > 2:
            if cluster not in diffex.keys():
                diffex[cluster] = get_cluster_differential_expression(
                    loom, clusteringlevel, layer, cluster)
            if np.sum(loom.ca[clusteringlevel] == cluster) > 1:
                genes = diffex[cluster][~diffex[cluster]['gene'].isin(
                    allgenes)].query('MeanExpr1 > MeanExpr2').query(
                        'FracExpr2<.9').head(10)['gene'].values
                genemask = np.isin(loom.ra['gene'], genes)
                rawX.append(
                    loom[layer][genemask, :][:, clusteredmask.nonzero()[0]])
                allgenes.append(genes)

    clusteredmask = np.hstack(clusteredmask)

    hmdf = pd.DataFrame(np.vstack(rawX))
    hmdf.index = np.hstack(allgenes)

    #fig, ax = plt.subplots(figsize=(5,12))
    fig = plt.figure(figsize=(5, 12))
    ax = fig.add_axes([0.4, 0.1, 0.4, .8])
    sns.heatmap(hmdf,
                cmap='coolwarm',
                yticklabels=1,
                xticklabels=False,
                ax=ax,
                cbar_kws={'label': r'log${}_2$(TP100k+1) Expression'})
    plt.ylabel('Gene')
    plt.xlabel('Cell')

    for i, cluster in enumerate(clusters):
        ax.annotate(
            cluster,
            xy=(-hmdf.shape[1] * 0.8,
                hmdf.shape[0] - ff_offset - 3.5 - i * ff_scale),
            xytext=(-hmdf.shape[1] * 0.9,
                    hmdf.shape[0] - ff_offset - 3.5 - i * ff_scale),
            ha='right',
            va='center',
            bbox=dict(boxstyle='square', fc='white'),
            arrowprops=dict(
                arrowstyle='-[, widthB={}, lengthB=1.5'.format(bracket_width),
                lw=2.0),
            annotation_clip=False)
    #plt.savefig("./figures/AllCD8TCellClustersHeatmap14Sept2020.pdf")
    if output is not None:
        plt.savefig(output)
    plt.show()
    return diffex

    #print(expr)

    ax.set_xticklabels(markernames)
    ax.set_xticks(range(len(markers)))
    ax.set_yticklabels(
        [key for key in key2x.keys() if key not in keyblacklist])
    #print(np.array([val for val in diffex.values() if key not in keyblacklist]))
    ax.set_yticks(
        np.array([val for val in key2x.values() if key not in keyblacklist]))
    ax.set_xlim([-0.5, len(markers) - 0.5])
    ax.set_ylim([-0.5, len(key2x) - 0.5])
    for i in np.arange(-0.5, len(markers) - 0.5, topn)[1::]:
        plt.axvline(ls='--', x=i, color='k')
        #if flag:
    cbar = plt.colorbar(sc, )
    cbar.set_label(
        'Mean {} Expression'.format(layername),
        rotation=90,
    )
    plt.xticks(rotation=90)
    if output is not None:
        plt.savefig(output)
    if title is not None:
        plt.title(title)
    plt.show()


def swarmviolin(data,
                x,
                y,
                hue=None,
                ax=None,
                split=False,
                alpha=0.2,
                noswarm=False,
                violinplot_kwargs={},
                swarmplot_kwargs={},
                swarm_downsample_percentage=None,
                annotate_hue_pvalues=False,
                annotate_hue_effect_size=False,
                annotate_hue_pvalue_fmt_str='p: {0:.2f}',
                annotate_hue_effect_size_fmt_str='es: {0:.2f}',
                effect_size='cohensd'):
    """

    Parameters
    ----------
    data :
        type data: pandas dataframe in form that would be acceptable input to seaborn violin, swarmplots
    diffex :
        param x:
    y :
        type y: column of data to be used for violin, swarmplot y argument
    hue : column of data to be used for violin, swarmplot hue argument
        Default value = 10)
    ax : matplotlib axis
        Default value = None)
    split : split: split argument to be passed to violin, swarmplot
        Default value = True)
    alpha : alpha: alpha to be used for seaborn violinplot
        Default value = 0.2)
    violinplot_kwargs :
        Default value = {})
    swarmplot_kwargs :
        Default value = {})
    swarm_downsample_percentage :
        Default value = None)
    annotate_hue_pvalues :
        Default value = False)
    annotate_hue_pvalue_fmt_str :
        Default value = 'p: {0:.2f}')
    x :
        
    noswarm :
        (Default value = False)
    annotate_hue_effect_size :
        (Default value = False)
    annotate_hue_effect_size_fmt_str :
        (Default value = 'es: {0:.2f}')
    effect_size : If annotating the effect size between hues, this will set the relevant means of calculation.  Must be one of 'cohensd' or 'cles' for Cohen's d, or common language effect size, respectively.
        (Default value = 'cohensd')

    Returns
    -------

    
    """
    import seaborn as sns
    import matplotlib.pyplot as plt
    if ax is None:
        fig, ax = plt.subplots(figsize=(5, 5))
    if hue is None:
        hue_order = None
    else:
        hue_order = data[hue].unique()
    sns.violinplot(data=data,
                   x=x,
                   hue=hue,
                   hue_order=hue_order,
                   y=y,
                   split=split,
                   inner='quartile',
                   cut=0,
                   alpha=alpha,
                   ax=ax,
                   width=.8,
                   **violinplot_kwargs)
    for violin in ax.collections:
        violin.set_alpha(alpha)
    if not noswarm:
        if swarm_downsample_percentage is None:
            sns.swarmplot(
                data=data,
                x=x,
                hue=hue,
                hue_order=hue_order,
                y=y,
                split=split,
                alpha=1,
                ax=ax,
                dodge=True,
                #          size=2.5,
                **swarmplot_kwargs)
        else:
            downsample_mask = np.random.choice(
                [True, False],
                size=data.shape[0],
                p=[
                    swarm_downsample_percentage,
                    1 - swarm_downsample_percentage
                ],
            )
            sns.swarmplot(data=data[downsample_mask],
                          x=x,
                          hue=hue,
                          hue_order=hue_order,
                          y=y,
                          split=split,
                          alpha=1,
                          ax=ax,
                          dodge=True,
                          **swarmplot_kwargs)

    def legend_without_duplicate_labels(ax):
        """

        Parameters
        ----------
        ax :
            

        Returns
        -------

        
        """
        handles, labels = ax.get_legend_handles_labels()
        unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels))
                  if l not in labels[:i]]
        ax.legend(*zip(*unique), title='', loc=(1.05, .8))

    legend_without_duplicate_labels(ax)
    if annotate_hue_pvalues or annotate_hue_effect_size:
        if len(data[hue].unique()) != 2:
            raise Exception(
                "hue must be a categorical variable with 2 unique values")
        from scipy.stats import mannwhitneyu
        print(data[y].dtype)
        if np.issubdtype(data[y].dtype, np.number):
            category_col = x
            continuous_col = y
            vertical_violins = True
            ticklabels = ax.get_xmajorticklabels()
        else:
            category_col = y
            continuous_col = x
            vertical_violins = False
            ticklabels = ax.get_ymajorticklabels()
        for ticklabel in ticklabels:
            category = ticklabel.get_text()
            hue1, hue2 = data[hue].unique()

            a = data[(data[hue] == hue1)
                     & (data[category_col] == category)][continuous_col].values
            b = data[(data[hue] == hue2)
                     & (data[category_col] == category)][continuous_col].values
            mw = mannwhitneyu(a, b, alternative='two-sided')
            pval = mw.pvalue
            if effect_size == 'cohensd':
                from panopticon.utilities import cohensd
                es = cohensd(a, b)
            elif effect_size == 'cles':
                es = mw.statistic / len(a) / len(b)
            else:
                raise Exception(
                    "effect_size must be either \'cohensd\' or \'cles\'")
            annotation_string = ''
            if vertical_violins:
                if annotate_hue_pvalues:
                    annotation_string += annotate_hue_pvalue_fmt_str.format(
                        pval) + '\n'
                if annotate_hue_effect_size:
                    annotation_string += annotate_hue_effect_size_fmt_str.format(
                        es) + '\n'
                ax.annotate(
                    annotation_string,
                    (ticklabel.get_position()[0], np.max(np.hstack((a, b)))),
                    ha='center',
                    va='bottom')
            else:
                if annotate_hue_pvalues:
                    annotation_string += ' ' + annotate_hue_pvalue_fmt_str.format(
                        pval)
                if annotate_hue_effect_size:
                    annotation_string += '\n ' + annotate_hue_effect_size_fmt_str.format(
                        es)
                ax.annotate(annotation_string, (
                    np.max(np.hstack((a, b))),
                    ticklabel.get_position()[1],
                ),
                            ha='left',
                            va='center')

    return ax


def volcano(diffex,
            ax=None,
            gene_column='gene',
            pval_column='pvalue',
            mean_expr_left='MeanExpr1',
            mean_expr_right='MeanExpr2',
            left_name='',
            right_name='',
            genemarklist=[],
            logfoldchange_importance_threshold=0.5,
            neglogpval_importance_threshold=5,
            title='',
            output=None,
            positions=None,
            show=True,
            gene_label_offset_scale=1):
    """

    Parameters
    ----------
    diffex :
        param ax:  (Default value = None)
    gene_column :
        Default value = 'gene')
    pval_column :
        Default value = 'pvalue')
    mean_expr_left :
        Default value = 'MeanExpr1')
    mean_expr_right :
        Default value = 'MeanExpr2')
    left_name : Genes toward the left in the volcano plot, which are upregulated in group2 of 'diffex'
        Default value = '')
    right_name : Genes toward the right in the volcano plot, which are upregulated in group1 of 'diffex'
        Default value = '')
    genemarklist :
        Default value = [])
    logfoldchange_importance_threshold :
        Default value = 0.5)
    neglogpval_importance_threshold :
        Default value = 5)
    title :
        Default value = '')
    output :
        Default value = None)
    positions :
        Default value = None)
    show :
        Default value = True)
    gene_label_offset_scale :
        Default value = 1)
    ax :
        (Default value = None)

    Returns
    -------

    
    """

    import matplotlib.pyplot as plt
    import matplotlib
    import matplotlib.patheffects as pe

    matplotlib.rcParams['axes.linewidth'] = 3
    if ax is None:
        fig, ax = plt.subplots(figsize=(
            5,
            5,
        ))
    neglogpvalues = -np.log(diffex[pval_column].values) / np.log(10)
    logfoldchange = diffex[mean_expr_left].values - diffex.MeanExpr2.values
    important_mask = (np.abs(logfoldchange) >
                      logfoldchange_importance_threshold)
    important_mask = important_mask & (neglogpvalues >
                                       neglogpval_importance_threshold)
    ax.scatter(logfoldchange[important_mask],
               neglogpvalues[important_mask],
               alpha=1,
               marker='.',
               s=3,
               c='b')
    ax.scatter(logfoldchange[~important_mask],
               neglogpvalues[~important_mask],
               alpha=.1,
               marker='.',
               s=2,
               c='b')
    maxx = np.nanmax(np.abs(logfoldchange))
    maxy = np.nanmax(neglogpvalues)
    print(maxx, maxy)
    xoffset = .1
    yoffset = .1
    offsetcounter = 0
    offsetcounter2 = 0
    #noteable_genes = diffex[diffex[gene_column].isin(genemarklist)].sort_values(pval_column)[gene_column].values
    if positions is None:
        positions = ['t'] * len(genemarklist)

    for gene, position in zip(
            genemarklist,
            positions,
    ):
        genedf = diffex[diffex[gene_column] == gene]
        negpval = -np.log(genedf.iloc[0][pval_column]) / np.log(10)
        logfoldchange = genedf.iloc[0].MeanExpr1 - genedf.iloc[0].MeanExpr2
        ax.scatter(logfoldchange, negpval, marker='.', color='k')
        if position == 'b':
            ax.annotate(
                gene, (logfoldchange, negpval),
                (logfoldchange,
                 negpval + .015 * maxy * gene_label_offset_scale),
                va='bottom',
                ha='center',
                path_effects=[pe.withStroke(linewidth=1, foreground="white")])
        elif position == 't':
            ax.annotate(
                gene, (logfoldchange, negpval),
                (logfoldchange,
                 negpval - .015 * maxy * gene_label_offset_scale),
                va='top',
                ha='center',
                path_effects=[pe.withStroke(linewidth=1, foreground="white")])
        elif position == 'l':
            ax.annotate(
                gene, (logfoldchange, negpval),
                (logfoldchange + .03 * maxx * gene_label_offset_scale,
                 negpval),
                va='center',
                ha='left',
                path_effects=[pe.withStroke(linewidth=1, foreground="white")])
        elif position == 'r':
            ax.annotate(
                gene, (logfoldchange, negpval),
                (logfoldchange - .03 * maxx * gene_label_offset_scale,
                 negpval),
                va='center',
                ha='right',
                path_effects=[pe.withStroke(linewidth=1, foreground="white")])
        else:
            raise Exception("invalid position character selection")
    plt.axvline(0, ls='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.tick_params(axis='both', which='minor', labelsize=14)
    ax.set_xlabel('log fold change\n' + '$\leftarrow$' + left_name + '\n' +
                  right_name + r'$\rightarrow$',
                  fontsize=14)

    ax.set_ylabel('-log' + r'${}_{10}$' + '(p-value)', fontsize=14)

    ax.set_xlim([-maxx * 1.04, maxx * 1.04])
    ax.set_ylim([0, maxy * 1.01])
    plt.tight_layout()
    ax.set_title(title)
    if output is not None:
        plt.savefig(output, bbox_inches='tight', transparent='true', dpi=300)
    if show:
        plt.show()


def repertoire_plot(x=None,
                    y=None,
                    data=None,
                    hue=None,
                    ax=None,
                    fig=None,
                    show=False,
                    output=None,
                    normalize=False,
                    piechart=False,
                    ylabel='',
                    legend=False,
                    color_palette=None,
                    stack_order='agnostic'):
    """Repertoire plot, designed for plotting cluster compositions or TCR repertoires as stacked bar plots or pies, with stack height indicating the size of a given TCR clone.  See https://doi.org/10.1101/2021.08.25.456956, Fig. 3e.  In this context, input should consist of a dataframe ('data'), with each row representing a cell.  Argument 'y' should be a column of 'data' representing the cell's clone or other grouping of cells.  Argument 'x' should be a column of 'data' representing the sample whence the cell came.

    Parameters
    ----------
    x : Column of data indicating sample
        Default value = None)
    y : Column of data indicate clone
        Default value = None)
    data : pandas.DataFrame object, with necessary columns specified by arguments x, y.
        Default value = None)
    hue : Optional column of data indicating additional grouping of samples
        Default value = None)
    ax : matplotlib matplotlib.axes._subplots.AxesSubplot object or array thereof, optional
        Default value = None)
    fig : matplotlib.figure.Figure object, optional
        Default value = None)
    show : if 'True', will run matplotlib.show() upon completion
        Default value = False)
    output : argument to matplotlib.savefig
        Default value = None)
    normalize :
        (Default value = False)
    piechart :
        (Default value = False)
    ylabel :
        (Default value = '')
    legend :
        (Default value = False)
    color_palette :
        (Default value = None)
    stack_order :
        (Default value = 'agnostic')

    Returns
    -------

    
    """
    if x is None:
        raise Exception("x is a required argument")
    if y is None:
        raise Exception("y is a required argument")
    if data is None:
        raise Exception("data is a required argument")
    if output is not None:
        if type(output) != str:
            raise Exception(
                "argument \"output\" must be a string, representing a desired filename"
            )
    #if piechar

    import matplotlib.pyplot as plt
    from tqdm import tqdm
    import matplotlib.transforms as transforms

    if ax is None and fig is not None:
        raise Exception(
            "argument \"ax\" must be included when argument \"fig\" is included"
        )
    elif fig is None and ax is not None:
        raise Exception(
            "argument \"ax\" must be included when argument \"fig\" is included"
        )
    if piechart and ax is not None:
        if type(ax) not in [np.ndarray, list]:
            raise Exception(
                "ax must be a list or array of matplotlib.axes._subplots.AxesSubplot objects when argument piechart==True"
            )
    if piechart and not normalize:
        print(
            "Warning: Pie charts must be normalized, because they are pie charts."
        )
    if stack_order not in ['matched', 'agnostic']:
        raise Exception("stack_order must be one of \'matched\', \'agnostic\'")
    if color_palette is None:
        if stack_order == 'matched':
            import seaborn as sns
            color_palette = sns.palettes.color_palette('colorblind')
        elif stack_order == 'agnostic':
            color_palette = ['w']

    all_heights = []

    if hue is None:
        if stack_order == 'agnostic':
            grouped_data = data.groupby(x)[y].value_counts()
        elif stack_order == 'matched':
            grouped_data = data.groupby(x)[y].value_counts(sort=False)

            # this code ensures that all categories are represented (even with 0) in all bars
            newname = "{}_{} count".format(x, y)  # to cover an edge case
            original_order = data[y].unique()
            grouped_data_df = grouped_data.rename(newname).reset_index()
            all_y = grouped_data_df[y].unique()
            grouped_data_df_dict = grouped_data_df.groupby(
                x)[y].unique().to_dict()
            for key in grouped_data_df_dict:
                for missing_element in np.setdiff1d(
                        all_y, grouped_data_df_dict[key]
                ):  # may fail if cluster name are of different types
                    zero_count_insert = pd.DataFrame(
                        np.array([key, missing_element, 0]).reshape(1, -1),
                        columns=grouped_data_df.columns).astype(
                            grouped_data_df.dtypes)
                    grouped_data_df = pd.concat(
                        [grouped_data_df, zero_count_insert], )
            y_to_original_order = {x: i for i, x in enumerate(original_order)}
            grouped_data_df = grouped_data_df.sort_values(
                y, key=np.vectorize(lambda x: y_to_original_order[x]))
            grouped_data = grouped_data_df.set_index([x, y])[newname]

        total = data.groupby(x)[y].unique().apply(lambda x: len(x)).max()
        groupings = data[x].unique()
        ind = np.arange(len(groupings))

    else:
        if stack_order == 'agnostic':
            grouped_data = data.groupby([x, hue])[y].value_counts()
        elif stack_order == 'matched':
            grouped_data = data.groupby([x, hue])[y].value_counts(sort=False)
            original_order = data[y].unique()
            newname = "{}_{}_{} count".format(x, y,
                                              hue)  # to cover an edge case
            grouped_data_df = grouped_data.rename(newname, ).reset_index()
            all_y = grouped_data_df[y].unique()
            grouped_data_df_dict = grouped_data_df.groupby(
                [x, hue])[y].unique().to_dict()

            for key in grouped_data_df_dict:
                for missing_element in np.setdiff1d(
                        all_y, grouped_data_df_dict[key]
                ):  # may fail if cluster name are of different types
                    zero_count_insert = pd.DataFrame(
                        np.array([key[0], key[1], missing_element,
                                  0]).reshape(1, -1),
                        columns=grouped_data_df.columns).astype(
                            grouped_data_df.dtypes)
                    grouped_data_df = pd.concat(
                        [grouped_data_df, zero_count_insert], )
            y_to_original_order = {x: i for i, x in enumerate(original_order)}
            grouped_data_df = grouped_data_df.sort_values(
                y, key=np.vectorize(lambda x: y_to_original_order[x]))
            grouped_data = grouped_data_df.set_index([x, hue, y])[newname]

        total = data.groupby([x,
                              hue])[y].unique().apply(lambda x: len(x)).max()
        groupings = list(data.groupby([x, hue]).groups.keys())
        ind = []
        counter = -1
        for i, grouping in enumerate(groupings):
            if grouping[0] != groupings[i - 1][0]:
                counter += 1
            ind.append(counter)
            counter += 1
        ind = np.array(ind)
# return grouped_data
    for grouping in groupings:
        heights = []
        for n in grouped_data[grouping].values:
            heights.append(n)
        heights = heights + [0] * (total - len(heights))
        heights = np.array(heights)[::-1]
        all_heights.append(heights)
    all_heights = np.vstack(all_heights)
    all_heights = all_heights[:, ::-1]
    if normalize:
        all_heights = np.divide(all_heights.T, all_heights.sum(axis=1)).T

    bottoms = np.array([0.0] * all_heights.shape[0])

    if (not piechart) and (ax is None) and (fig is None):
        fig, ax = plt.subplots(figsize=(5, 5))
    elif (piechart) and (ax is None) and (fig is None):
        import math
        ngroups = len(groupings)

        nrows = int(np.round(ngroups / np.sqrt(ngroups)))
        ncols = math.ceil(ngroups / np.sqrt(ngroups))
        print(ngroups, nrows, ncols)

        fig, ax = plt.subplots(nrows, ncols, figsize=(5, 5))


# if piechart:
#color = 'w'
    if piechart:
        for i in tqdm(range(all_heights.shape[0])):
            if stack_order == 'matched':
                labels = grouped_data[grouping].index.values
            else:
                labels = None
            if len(np.shape(ax)) == 1:
                ax[i].pie(all_heights[i, :],
                          colors=color_palette,
                          wedgeprops={"edgecolor": "k"},
                          labels=labels)
            elif len(np.shape(ax)) == 2:
                maxrows, maxcols = np.shape(ax)
                if all_heights.shape[0] // maxrows > maxcols:
                    raise Exception(
                        "Insufficient number of subplots for number of grouping (pies)"
                    )
                ax[i % maxrows,
                   i // maxrows].pie(all_heights[i, :],
                                     colors=color_palette,
                                     wedgeprops={"edgecolor": "k"},
                                     labels=labels)
                #edgecolor='k')
                ax[i % maxrows, i // maxrows].set_title(groupings[i])

    else:  # conventional stacked bar plot mode
        for i in tqdm(range(all_heights.shape[1])):

            #from IPython.core.debugger import set_trace; set_trace()
            if stack_order == 'matched':
                label = grouped_data[grouping].index[i]
            else:
                label = None
            ax.bar(ind,
                   all_heights[:, i],
                   0.8,
                   bottom=bottoms,
                   color=color_palette[i % len(color_palette)],
                   edgecolor='k',
                   label=label)

            bottoms += all_heights[:, i]
        ax.set_xticks(ind)
        if hue is None:
            ax.set_xticklabels(groupings, rotation=90)
        else:
            ax.set_xticklabels([grouping[1] for grouping in groupings],
                               rotation=90)
            plt.tight_layout()

            xpositions = []
            labels = []
            xpos = 0
            for i, grouping in enumerate(groupings):
                if grouping[0] != groupings[i - 1][0]:
                    xpositions.append(i)
                    labels.append(grouping[0])
            xpositions.append(len(groupings))
            xpositions = np.array(xpositions)[0:-1] + np.diff(xpositions) * 0.5
            xpositions += np.arange(len(xpositions))
            xpositions -= 0.5
            for xposition, label in zip(xpositions, labels):
                trans = transforms.blended_transform_factory(
                    ax.transData, fig.transFigure)

                ax.annotate(label, (xposition, 0),
                            annotation_clip=False,
                            ha='center',
                            va='bottom',
                            xycoords=trans,
                            fontsize=13)
        if ylabel == '':
            if normalize:
                ylabel = 'cell fraction'
            else:
                ylabel = 'cell count'
        ax.set_ylabel(ylabel)
    plt.tight_layout()
    if output is not None:

        if output.endswith('.png'):
            plt.savefig(output, dpi=300)
        else:
            plt.savefig(output)
    if show:
        plt.show()


def data_to_grid_kde(x, y, xmin=None, xmax=None, ymin=None, ymax=None, px=100):
    """

    Parameters
    ----------
    x : Vector
        
    y : Vector
        
    px :
        (Default value = 100)
    xmin :
         (Default value = None)
    xmax :
         (Default value = None)
    ymin :
         (Default value = None)
    ymax :
         (Default value = None)

    Returns
    -------

    
    """
    from scipy.stats import gaussian_kde
    xy = np.vstack((x, y))
    kde = gaussian_kde(xy)
    if np.any([z is None for z in [xmin, xmax, ymin, ymax]]):
        if np.all([z is None for z in [xmin, xmax, ymin, ymax]]):
            xmin, xmax = (x.min(), x.max())
            ymin, ymax = (y.min(), y.max())
        else:
            raise Exception(
                "Either all of xmin, xmax, ymin, ymax must be \"None\", or none may be."
            )
    xgrid = np.arange(xmin, xmax, (xmax - xmin) / px)
    ygrid = np.arange(ymin, ymax, (ymax - ymin) / px)
    xx, yy = np.meshgrid(xgrid, ygrid)
    zz = kde.evaluate(
        np.array([xx.reshape(-1, 1)[:, 0],
                  yy.reshape(-1, 1)[:, 0]])).reshape(xx.shape, )
    return zz


def plot_differential_density(x, y, mask1, mask2, ax=None, cmap=plt.cm.RdBu_r):
    """

    Parameters
    ----------
    x :
        
    y :
        
    mask1 :
        
    mask2 :
        
    ax :
         (Default value = None)
    cmap :
         (Default value = plt.cm.RdBu_r)

    Returns
    -------

    """
    xmin, xmax = (x.min(), x.max())
    ymin, ymax = (y.min(), y.max())

    import numpy as np
    from panopticon.visualization import data_to_grid_kde
    zz1 = data_to_grid_kde(x[mask1],
                           y[mask1],
                           xmin=xmin,
                           ymin=ymin,
                           xmax=xmax,
                           ymax=ymax)
    from panopticon.visualization import data_to_grid_kde
    zz2 = data_to_grid_kde(x[mask2],
                           y[mask2],
                           xmin=xmin,
                           ymin=ymin,
                           xmax=xmax,
                           ymax=ymax)
    vmin = np.min(zz1 - zz2)
    vmax = np.max(zz1 - zz2)
    if np.abs(vmax) > np.abs(vmin):
        vmin = -vmax
    else:
        vmax = -vmin
    if ax is None:
        plt.imshow(zz1 - zz2, origin='lower', cmap=cmap, vmin=vmin, vmax=vmax)
        plt.show()
    else:
        ax.imshow(zz1 - zz2, origin='lower', cmap=cmap, vmin=vmin, vmax=vmax)


def plot_density(x, y, ax=None, cmap=plt.cm.twilight_r):
    """

    Parameters
    ----------
    x :
        
    y :
        
    ax :
         (Default value = None)
    cmap :
         (Default value = plt.cm.twilight_r)

    Returns
    -------

    """

    from panopticon.visualization import data_to_grid_kde
    zz = data_to_grid_kde(x, y)
    if ax is None:
        plt.imshow(zz, origin='lower', cmap=cmap, vmin=vmin, vmax=vmax)
        plt.show()
    else:
        ax.imshow(zz, origin='lower', cmap=cmap, vmin=vmin, vmax=vmax)


def cluster_enrichment_heatmap(x,
                               y,
                               data,
                               show=True,
                               output=None,
                               fig=None,
                               cax=None,
                               ax=None,
                               side_annotation=True,
                               heatmap_shading_key='ClusterFraction',
                               annotation_key='Counts',
                               annotation_fmt='.5g'):
    """

    Parameters
    ----------
    x :
        
    y :
        
    data :
        
    show :
         (Default value = True)
    output :
         (Default value = None)
    fig :
         (Default value = None)
    cax :
         (Default value = None)
    ax :
         (Default value = None)
    side_annotation :
         (Default value = True)
    heatmap_shading_key :
         (Default value = 'ClusterFraction')
    annotation_key :
         (Default value = 'Counts')
    annotation_fmt :
         (Default value = '.5g')

    Returns
    -------

    """
    from panopticon.analysis import get_cluster_enrichment_dataframes
    import matplotlib.pyplot as plt
    import seaborn as sns

    cluster_enrichment_dataframes = get_cluster_enrichment_dataframes(
        x, y, data)
    if fig is None and cax is None and ax is None:
        fig, (cax,
              ax) = plt.subplots(nrows=2,
                                 figsize=(5, 5.025),
                                 gridspec_kw={"height_ratios": [0.025, 1]})
    elif fig is not None and cax is not None and ax is not None:
        pass
    else:
        raise Exception(
            'Either none of "fig", "ax", and "cax" must be None, or all must be'
        )

    if len(data[x].unique()) != 2 and side_annotation:
        raise Exception(
            "Side annotation only supported for data with two unique groups")

    if (heatmap_shading_key not in cluster_enrichment_dataframes._fields):
        raise Exception("heatmap_shading key must be one of {}".format(
            cluster_enrichment_dataframes._fields))
    if (annotation_key not in cluster_enrichment_dataframes._fields):
        raise Exception("annotation_key key must be one of {}".format(
            cluster_enrichment_dataframes._fields))

    sns.heatmap(cluster_enrichment_dataframes._asdict()[heatmap_shading_key],
                cmap='Blues',
                annot=cluster_enrichment_dataframes._asdict()[annotation_key],
                cbar=False,
                vmin=0,
                vmax=1,
                fmt=annotation_fmt)
    fig.colorbar(ax.get_children()[0],
                 cax=cax,
                 orientation="horizontal",
                 label='proportion of cells (in-cluster)')
    #      annotation_clip=False)    #scipy.stats.chisquare
    cax.xaxis.tick_top()
    cax.xaxis.set_label_position('top')
    if side_annotation:
        for (i, fep_row), (j, phi_row) in zip(
                cluster_enrichment_dataframes.FishersExactP.iterrows(),
                cluster_enrichment_dataframes.PhiCoefficient.iterrows()):
            phi = phi_row.values[0]
            pval = fep_row.values[0]
            ax.annotate('p = {0:.2e}, '.format(pval) + r'$\phi$' +
                        ' = {0:.4f}'.format(phi),
                        xy=(2, i + .5),
                        xytext=(2.3, i + .5),
                        ha='left',
                        va='center',
                        bbox=dict(boxstyle='square', fc='white', ec='black'),
                        arrowprops=dict(
                            arrowstyle='-[, widthB={}, lengthB=0'.format(1),
                            lw=2.0,
                            color='k'),
                        annotation_clip=False)  #scipy.stats.chisquare
    if output is not None:
        plt.tight_layout()
        plt.savefig(output)
    plt.show()
