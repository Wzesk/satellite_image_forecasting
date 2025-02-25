import sys
import os
import numpy as np
from matplotlib import gridspec
import datetime as dt

sys.path.append(os.getcwd())

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from load_model_data import *
year = "2020"
def main():
    filename = None
    truth, context, target, npf = load_data_point(test_context_dataset = "Data/small_data/extreme_context_data_paths.pkl", 
                                                  test_target_dataset = "Data/small_data/extreme_target_data_paths.pkl")

    dates_strings = ['2018-01-28','2018-11-23'] 

    model1 = load_model()
    #model2 = load_model("trained_models/autoencoder_26.ckpt")
    pred1, _, _ = model1(x = context, 
                       prediction_count = int((2/3)*truth.shape[-1]), 
                       non_pred_feat = npf)
    #pred2, _, _ = model2(x = context, 
    #                   prediction_count = int((2/3)*truth.shape[-1]), 
    #                   non_pred_feat = npf)
    truth_old= np.load("demos/sentinel_data_"+year+".npy").astype(float)
    truth_old = truth_old.transpose(2,0,1,3)[np.newaxis,...]


    plot_ndvi_mt(truth_old, truth, [pred1], dates_bound = dates_strings, model_names=["ConvLSTM","EncoderDecoderConvLSTM"])


    # take out cloudy days
    #splits = np.linspace(0.1,1,10)
    
def plot_ndvi_mt(old_truth, truth, preds, dates_bound = None, filename = None, model_names = None):

    
    ndvi_truth = ((truth[:, 3, ...] - truth[ :, 2, ...]) / (
            truth[:, 3, ...] + truth[:, 2, ...] + 1e-6))
    cloud_mask = 1 - truth[:, 4, ...]
    ndvi_truth = ndvi_truth*cloud_mask

    old_truth_ndvi = ((old_truth[:, 3, ...] - old_truth[ :, 2, ...]) / (
                old_truth[:, 3, ...] + old_truth[:, 2, ...] + 1e-6))
    cloud_mask = 1 - old_truth[:, 4, ...]/255
    old_truth_ndvi = old_truth_ndvi*cloud_mask

    if not isinstance(preds, list):
        preds = [preds]

    if model_names is None:
        model_names = []
        for i in range(len(preds)):
            model_names.append("model {0}".format(i+1))
    
    colors = ["b","r","g","c","m","y"]
    colors = colors[:len(preds)]

    ndvi_preds = []
    for pred in preds:
        ndvi_preds.append(((pred[:, 3, ...] - pred[ :, 2, ...]) / (
                    pred[:, 3, ...] + pred[:, 2, ...] + 1e-6)))

    confidence = .5
    splits = [(1-confidence)/2, 0.5, 1 - (1-confidence)/2]
    q_t = np.quantile(ndvi_truth, splits, axis = (0,1,2))
    q_t_old = np.quantile(old_truth_ndvi, splits, axis = (0,1,2))

    valid_ndvi_time = q_t[0]!=0
    q_t[0,valid_ndvi_time]

    valid_ndvi_time_old = q_t_old[0]!=0
    q_t_old[0,valid_ndvi_time_old]

    x_t = np.arange(truth.shape[-1])[valid_ndvi_time]
    x_p = np.arange(truth.shape[-1] - pred.shape[-1], truth.shape[-1])

    def date_linspace(start, end, steps):
        delta = (end - start) / steps
        increments = range(0, steps) * np.array([delta]*steps)
        return start + increments

    if dates_bound is not None:
        dates_bound = [dt.datetime.strptime(dates_bound[0], '%Y-%m-%d'),dt.datetime.strptime(dates_bound[1], '%Y-%m-%d')] 
        dates = date_linspace(dates_bound[0],dates_bound[1],truth.shape[-1])

        x_t = dates[valid_ndvi_time]
        x_p = dates[int((1/3)*truth.shape[-1]):]
        x_old = dates[valid_ndvi_time_old]

    q_ps = []
    for ndvi_pred in ndvi_preds:
        q_ps.append(np.quantile(ndvi_pred.detach().numpy(), splits, axis = (0,1,2)))

    # plot pred and truth NDVI
    fig = plt.figure()
    # set height ratios for subplots
    gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1]) 

    # the first subplot
    ax0 = plt.subplot(gs[0])

    for q_p, mod_name, color in zip(q_ps, model_names, colors):
        ax0.plot(x_p, q_p[1,:], '--',color = color, label = mod_name)

    ax0.plot(x_t, q_t[1,valid_ndvi_time], '-',color = 'k', label = 'true median')
    ax0.plot(x_old, q_t_old[1,valid_ndvi_time_old], '-',color = 'g', label = year + ' median')
    ax0.legend(loc="upper right")
    for q_p, color in zip(q_ps, colors):
        ax0.fill_between(x_p, q_p[0,:],q_p[2,:], color = color, alpha=.1)
    ax0.fill_between(x_t, q_t[0,valid_ndvi_time],q_t[2,valid_ndvi_time], color = 'k', alpha=.1)
    ax0.fill_between(x_old, q_t_old[0,valid_ndvi_time_old],q_t_old[2,valid_ndvi_time_old], color = 'g', alpha=.1)


    # Set the locator
    locator = mdates.MonthLocator()  # every month
    # Specify the format - %b gives us Jan, Feb...
    fmt = mdates.DateFormatter('%b')
    # log scale for axis Y of the first subplot

    # the second subplot
    X = ax0.xaxis
    X.set_major_locator(locator)
    X.set_major_formatter(fmt)
    # shared axis X
    ax1 = plt.subplot(gs[1], sharex = ax0)
    ax2 = plt.subplot(gs[2], sharex = ax0)

    ax0.grid()
    ax1.grid()
    ax2.grid()
    if dates_bound is None:
        ax1.plot(np.arange(truth.shape[-1]-1)+1 , 50 * truth[0,6,0,0,:-1], label = 'precipitation')
        ax2.plot(np.arange(truth.shape[-1]-1)+1 , 50 *(2*truth[0,8,0,0,:-1] - 1), label = 'mean temp')
    else:
        ax1.plot(dates[1:] , 50 * truth[0,6,0,0,:-1], label = 'precipitation')
        ax2.plot(dates[1:] , 50 *(2*truth[0,8,0,0,:-1] - 1), label = 'mean temp')

    ax0.set_ylabel("NDVI")
    ax1.set_ylabel("Rain" +"\n" + "(mm)")
    ax2.set_ylabel("Temp" +"\n" + "(°C)")
    ax2.set_xlabel("Time")

    # Set the locator
    locator = mdates.MonthLocator()  # every month
    # Specify the format - %b gives us Jan, Feb...
    fmt = mdates.DateFormatter('%b')
    # log scale for axis Y of the first subplot

    # the second subplot
    X = ax2.xaxis
    X.set_major_locator(locator)
    X.set_major_formatter(fmt)

    #plt.xlim([0, truth.size()[-1]])

    plt.setp(ax0.get_xticklabels(), visible=False)
    plt.setp(ax1.get_xticklabels(), visible=False)
    # remove last tick label for the second subplot
    '''
    yticks = ax1.yaxis.get_major_ticks()
    yticks[-1].label1.set_visible(False)'''

    # put legend on first subplot
    #ax0.legend((line0, line1), ('red line', 'blue line'), loc='lower left')

    # remove vertical gap between subplots
    plt.subplots_adjust(hspace=.0)

    plt.xlim([x_t[0],x_t[-1]]) #only to see the legal part.

    if filename == None:
        plt.savefig("NDVI_time_series"+year+".pdf", format="pdf")
        plt.show()
    else:
        plt.savefig(filename)
    
    print("Done")

main()