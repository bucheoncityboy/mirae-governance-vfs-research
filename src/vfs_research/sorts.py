from .universe import pbr


def classify(d, g_quantile=.5, size_neutral=False):
    q=d.copy();q['pbr']=pbr(q)
    q['pbr_group']=q.pbr.gt(q.pbr.median()).map({False:'Low',True:'High'})
    q['cell']='';q['g_cut_value']=float('nan')
    for _, x in q.groupby('pbr_group'):
        parts = [x]
        if size_neutral:
            parts=[x.loc[x.lag_me.le(x.lag_me.median())],x.loc[x.lag_me.gt(x.lag_me.median())]]
        for z in parts:
            if z.empty:continue
            cut=z.g_value.quantile(g_quantile)
            q.loc[z.index,'g_cut_value']=cut
            q.loc[z.index,'cell']=z.pbr_group+'-'+z.g_value.gt(cut).map({True:'Good',False:'Bad'})
    return q
