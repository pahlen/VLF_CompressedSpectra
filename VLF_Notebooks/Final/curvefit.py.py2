import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
class curvefit(object):
    '''The curve in a loglog to be fitted with a high degree polynomial
       In the $(\log x,\log y)$-plane one straight line is described by $y = Ae^{Bx}$ for some $A$ and $B$.

       From: http://stackoverflow.com/a/3433503/2268280:

       For fitting $y = Ae^{Bx}$, take the logarithm of both side gives $\log y = \log A + Bx$. 
       So just fit $\log y$ against $x$.
    '''
    coeffs=np.array(0)
    def __init__(self,x=[],y=[]):
        self.x=np.asarray(x)
        self.y=np.asarray(y)
        #if self.x.shape[0]>0:
        #    self.corners=np.append(self.corners,self.x[0])
    def __getitem__(self, key):
        if key=='x':
            return self.x
        elif key=='y': 
            return self.y
        elif key=='coeffs':
            return self.coeffs
        else:
            sys.exit('Not key: %s' %key)
            
    def add_fit(self,poly_order=1,ShowPlot=True,verbose=False):
        '''Add one logarhitmic fit
           ShowPlot to check the fit
        '''

        
        self.coeffs = np.polyfit(np.log10(self.x), np.log10(self.y), poly_order)
        self.poly1d = np.poly1d(self.coeffs)
        if verbose:
            print 'logy=',p
        if ShowPlot:
            xlog=np.logspace( np.log10( self.x.min() ),np.log10( self.x.max() ) )
            plt.loglog(self.x,self.y,'ro')
            plt.loglog( xlog,10**( self.poly1d( np.log10(xlog) ) ) )
        return self.poly1d
    
    def to_csv(self,csvfile):
        '''
        Save the fit data to a csv file with colums:
        coeffs
        which are the coefficients array for np.poly1d
        '''
        df=pd.DataFrame()
        df['coeffs']=self.coeffs
        df.to_csv(csvfile,index=False)
        
    def read_csv(self,csvfile):
        '''
        Recover fitted data from a csv file with colums:
        coeffs
        which are the coefficients array for np.poly1d
        '''
        df=pd.read_csv(csvfile)
        self.coeffs=df.coeffs
        self.poly1d = np.poly1d(self.coeffs)
        
    def __call__(self,x):
        '''
        Given an array A and another array B defined by the
        values of x in corners, obtain the several values
        of $y = Ae^{Bx}$ for any x.
        x can be a float or an array of floats
        '''
        if self.coeffs.shape:
            return 10**( self.poly1d( np.log10(x) ) )
        else:
            sys.exit('Intialize the object with arrays or file')

