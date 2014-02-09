import pylab

pylab.figure(figsize=(6,3))
pylab.axes((0.12, 0.18, 0.8, 0.75))

xdata = [0,1,2,3,4,5,6]
xlabels = ['1,000','2,000','5,000','10,000','20,000','50,000','100,000']

noise = [0.9531939304739, 0.77672907350230003, 0.44532521750749998, 0.2993310309021, 0.21452009145110001, 0.1246532696683, 0.094993033319469983]

noise_ci = [[-0.046382024456799953, -0.03403479718369995, -0.014646186376500059, -0.022973793091299988, -0.015859146417200043, -0.011102312081200008, -0.0064215230513600258],[-0.067746337590200101, -0.039363065289499954, -0.015491345863499983, -0.017577160194300057, -0.018637057637600041, -0.0084761992000000064, -0.009037026284299976]]

noise_high = [noise[i]-noise_ci[0][i] for i in range(len(xdata))]
noise_low = [noise[i]+noise_ci[1][i] for i in range(len(xdata))]


pylab.plot(xdata, noise, color='k')
#pylab.errorbar(xdata,retry,yerr=retry_ci)
pylab.fill_between(xdata, noise_high, noise_low, facecolor='k', alpha=0.5)

pylab.xlabel('neurons')
pylab.ylabel('noise in stored vector')
pylab.xticks(xdata, xlabels)
pylab.savefig('figure2.png', dpi=900)
pylab.show()