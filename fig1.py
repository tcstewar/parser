import pylab

pylab.figure(figsize=(6,4))
pylab.axes((0.1, 0.15, 0.85, 0.8))

xdata = [0, 0.05, 0.1, 0.15, 0.2, 0.25]
prob = [0.8460282942701628, 0.82180483919511071, 0.76707987722978233, 0.68378508230323654, 0.55306743181409768, 0.38986098204964698]
prob_ci = [[-0.014085009764384537, -0.018748421744134269, -0.020100806791683468, -0.019680248650571164, -0.019543693497638293, -0.015030066427057398],[-0.01285147459159508, -0.011726667849281225, -0.017260737163283912, -0.017229313094358378, -0.015767339932743041, -0.018808090677573441]]

prob_high = [prob[i]-prob_ci[0][i] for i in range(len(xdata))]
prob_low = [prob[i]+prob_ci[1][i] for i in range(len(xdata))]


#pylab.errorbar(xdata,[0.8460282942701628, 0.82180483919511071, 0.76707987722978233, 0.68378508230323654, 0.55306743181409768, 0.38986098204964698],yerr=prob_ci)



retry = [0.60392156862745094, 0.66470588235294115, 0.62352941176470589, 0.70588235294117652, 0.92941176470588238, 0.98235294117647054]
retry_ci = [[-0.086274509803921595, -0.090196078431372562, -0.098039215686274495, -0.11176470588235288, -0.14117647058823524, -0.12745098039215697],[-0.094117647058823528, -0.084313725490196001, -0.074509803921568585, -0.074509803921568696, -0.11372549019607847, -0.13529411764705879]]

retry_high = [retry[i]-retry_ci[0][i] for i in range(len(xdata))]
retry_low = [retry[i]+retry_ci[1][i] for i in range(len(xdata))]


pylab.plot(xdata, retry, color='b', label='retry')
#pylab.errorbar(xdata,retry,yerr=retry_ci)
pylab.fill_between(xdata, retry_high, retry_low, facecolor='b', alpha=0.3)

pylab.plot(xdata,prob, color='k', linewidth=1)
pylab.fill_between(xdata, prob_high, prob_low, facecolor='k', alpha=0.5)

pylab.ylim(0.3, 1.2)

retry_rect = pylab.Rectangle((0, 0), 1, 1, fc="b", alpha=0.3)
prob_rect = pylab.Rectangle((0, 0), 1, 1, fc="k", alpha=0.5)
pylab.legend([prob_rect, retry_rect], ['parse probability', "# of retries"], loc='upper left')
pylab.xlabel('noise')
pylab.savefig('figure1.png', dpi=900)
pylab.show()