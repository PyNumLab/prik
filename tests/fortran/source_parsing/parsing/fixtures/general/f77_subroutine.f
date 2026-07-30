      subroutine daxpy(n,a,x,y)
      integer n
      double precision a,x(n),y(n)
      do 10 i=1,n
     1y(i)=y(i)+a*x(i)
 10   continue
      return
      end
