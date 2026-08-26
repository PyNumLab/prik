module fmath_arrays_f90
contains
      SUBROUTINE SQUARE_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 10 I = 1, N
         R(I) = X(I) * X(I)
10    CONTINUE

      RETURN
      END


      SUBROUTINE SQUARE_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 20 I = 1, N
         R(I) = X(I) * X(I)
20    CONTINUE

      RETURN
      END


      SUBROUTINE SQUARE_I4_CONTIGUOUS(N, X, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 30 I = 1, N
         R(I) = X(I) * X(I)
30    CONTINUE

      RETURN
      END


      SUBROUTINE SQUARE_C4_CONTIGUOUS(N, Z, R)
      INTEGER N
      COMPLEX, CONTIGUOUS :: Z(:)
      COMPLEX, CONTIGUOUS :: R(:)

      DO 40 I = 1, N
         R(I) = Z(I) * Z(I)
40    CONTINUE

      RETURN
      END


      SUBROUTINE SQUARE_C8_CONTIGUOUS(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX, CONTIGUOUS :: Z(:)
      DOUBLE COMPLEX, CONTIGUOUS :: R(:)

      DO 50 I = 1, N
         R(I) = Z(I) * Z(I)
50    CONTINUE

      RETURN
      END


      SUBROUTINE CUBE_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 60 I = 1, N
         R(I) = X(I) * X(I) * X(I)
60    CONTINUE

      RETURN
      END


      SUBROUTINE CUBE_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 70 I = 1, N
         R(I) = X(I) * X(I) * X(I)
70    CONTINUE

      RETURN
      END


      SUBROUTINE CUBE_I4_CONTIGUOUS(N, X, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 80 I = 1, N
         R(I) = X(I) * X(I) * X(I)
80    CONTINUE

      RETURN
      END


      SUBROUTINE ADD_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 90 I = 1, N
         R(I) = X(I) + Y(I)
90    CONTINUE

      RETURN
      END


      SUBROUTINE ADD_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 100 I = 1, N
         R(I) = X(I) + Y(I)
100   CONTINUE

      RETURN
      END


      SUBROUTINE ADD_I4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: Y(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 110 I = 1, N
         R(I) = X(I) + Y(I)
110   CONTINUE

      RETURN
      END


      SUBROUTINE ADD_C4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      COMPLEX, CONTIGUOUS :: X(:)
      COMPLEX, CONTIGUOUS :: Y(:)
      COMPLEX, CONTIGUOUS :: R(:)

      DO 120 I = 1, N
         R(I) = X(I) + Y(I)
120   CONTINUE

      RETURN
      END


      SUBROUTINE ADD_C8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE COMPLEX, CONTIGUOUS :: X(:)
      DOUBLE COMPLEX, CONTIGUOUS :: Y(:)
      DOUBLE COMPLEX, CONTIGUOUS :: R(:)

      DO 130 I = 1, N
         R(I) = X(I) + Y(I)
130   CONTINUE

      RETURN
      END


      SUBROUTINE SUB_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 140 I = 1, N
         R(I) = X(I) - Y(I)
140   CONTINUE

      RETURN
      END


      SUBROUTINE SUB_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 150 I = 1, N
         R(I) = X(I) - Y(I)
150   CONTINUE

      RETURN
      END


      SUBROUTINE SUB_I4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: Y(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 160 I = 1, N
         R(I) = X(I) - Y(I)
160   CONTINUE

      RETURN
      END


      SUBROUTINE MUL_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 170 I = 1, N
         R(I) = X(I) * Y(I)
170   CONTINUE

      RETURN
      END


      SUBROUTINE MUL_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 180 I = 1, N
         R(I) = X(I) * Y(I)
180   CONTINUE

      RETURN
      END


      SUBROUTINE MUL_I4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: Y(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 190 I = 1, N
         R(I) = X(I) * Y(I)
190   CONTINUE

      RETURN
      END


      SUBROUTINE DIV_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 200 I = 1, N
         R(I) = X(I) / Y(I)
200   CONTINUE

      RETURN
      END


      SUBROUTINE DIV_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 210 I = 1, N
         R(I) = X(I) / Y(I)
210   CONTINUE

      RETURN
      END


      SUBROUTINE POW_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 220 I = 1, N
         R(I) = X(I) ** Y(I)
220   CONTINUE

      RETURN
      END


      SUBROUTINE POW_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 230 I = 1, N
         R(I) = X(I) ** Y(I)
230   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 240 I = 1, N
         R(I) = ABS(X(I))
240   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 250 I = 1, N
         R(I) = ABS(X(I))
250   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_I4_CONTIGUOUS(N, X, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 260 I = 1, N
         R(I) = ABS(X(I))
260   CONTINUE

      RETURN
      END


      SUBROUTINE NEG_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 270 I = 1, N
         R(I) = -X(I)
270   CONTINUE

      RETURN
      END


      SUBROUTINE NEG_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 280 I = 1, N
         R(I) = -X(I)
280   CONTINUE

      RETURN
      END


      SUBROUTINE NEG_I4_CONTIGUOUS(N, X, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 290 I = 1, N
         R(I) = -X(I)
290   CONTINUE

      RETURN
      END


      SUBROUTINE SIN_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 300 I = 1, N
         R(I) = SIN(X(I))
300   CONTINUE

      RETURN
      END


      SUBROUTINE SIN_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 310 I = 1, N
         R(I) = DSIN(X(I))
310   CONTINUE

      RETURN
      END


      SUBROUTINE COS_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 320 I = 1, N
         R(I) = COS(X(I))
320   CONTINUE

      RETURN
      END


      SUBROUTINE COS_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 330 I = 1, N
         R(I) = DCOS(X(I))
330   CONTINUE

      RETURN
      END


      SUBROUTINE TAN_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 340 I = 1, N
         R(I) = TAN(X(I))
340   CONTINUE

      RETURN
      END


      SUBROUTINE TAN_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 350 I = 1, N
         R(I) = DTAN(X(I))
350   CONTINUE

      RETURN
      END


      SUBROUTINE ASIN_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 360 I = 1, N
         R(I) = ASIN(X(I))
360   CONTINUE

      RETURN
      END


      SUBROUTINE ASIN_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 370 I = 1, N
         R(I) = DASIN(X(I))
370   CONTINUE

      RETURN
      END


      SUBROUTINE ACOS_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 380 I = 1, N
         R(I) = ACOS(X(I))
380   CONTINUE

      RETURN
      END


      SUBROUTINE ACOS_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 390 I = 1, N
         R(I) = DACOS(X(I))
390   CONTINUE

      RETURN
      END


      SUBROUTINE ATAN_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 400 I = 1, N
         R(I) = ATAN(X(I))
400   CONTINUE

      RETURN
      END


      SUBROUTINE ATAN_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 410 I = 1, N
         R(I) = DATAN(X(I))
410   CONTINUE

      RETURN
      END


      SUBROUTINE ATAN2_R4_CONTIGUOUS(N, Y, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 420 I = 1, N
         R(I) = ATAN2(Y(I), X(I))
420   CONTINUE

      RETURN
      END


      SUBROUTINE ATAN2_R8_CONTIGUOUS(N, Y, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 430 I = 1, N
         R(I) = DATAN2(Y(I), X(I))
430   CONTINUE

      RETURN
      END


      SUBROUTINE EXP_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 440 I = 1, N
         R(I) = EXP(X(I))
440   CONTINUE

      RETURN
      END


      SUBROUTINE EXP_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 450 I = 1, N
         R(I) = DEXP(X(I))
450   CONTINUE

      RETURN
      END


      SUBROUTINE LOG_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 460 I = 1, N
         R(I) = LOG(X(I))
460   CONTINUE

      RETURN
      END


      SUBROUTINE LOG_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 470 I = 1, N
         R(I) = DLOG(X(I))
470   CONTINUE

      RETURN
      END


      SUBROUTINE LOG10_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 480 I = 1, N
         R(I) = LOG10(X(I))
480   CONTINUE

      RETURN
      END


      SUBROUTINE LOG10_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 490 I = 1, N
         R(I) = DLOG10(X(I))
490   CONTINUE

      RETURN
      END


      SUBROUTINE SQRT_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)

      DO 500 I = 1, N
         R(I) = SQRT(X(I))
500   CONTINUE

      RETURN
      END


      SUBROUTINE SQRT_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 510 I = 1, N
         R(I) = DSQRT(X(I))
510   CONTINUE

      RETURN
      END


      SUBROUTINE HYPOT_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 520 I = 1, N
         R(I) = SQRT(X(I) * X(I) + Y(I) * Y(I))
520   CONTINUE

      RETURN
      END


      SUBROUTINE HYPOT_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 530 I = 1, N
         R(I) = DSQRT(X(I) * X(I) + Y(I) * Y(I))
530   CONTINUE

      RETURN
      END


      SUBROUTINE MIN_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 540 I = 1, N
         R(I) = MIN(X(I), Y(I))
540   CONTINUE

      RETURN
      END


      SUBROUTINE MIN_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 550 I = 1, N
         R(I) = DMIN1(X(I), Y(I))
550   CONTINUE

      RETURN
      END


      SUBROUTINE MIN_I4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: Y(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 560 I = 1, N
         R(I) = MIN(X(I), Y(I))
560   CONTINUE

      RETURN
      END


      SUBROUTINE MAX_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 570 I = 1, N
         R(I) = MAX(X(I), Y(I))
570   CONTINUE

      RETURN
      END


      SUBROUTINE MAX_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 580 I = 1, N
         R(I) = DMAX1(X(I), Y(I))
580   CONTINUE

      RETURN
      END


      SUBROUTINE MAX_I4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: Y(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 590 I = 1, N
         R(I) = MAX(X(I), Y(I))
590   CONTINUE

      RETURN
      END


      SUBROUTINE SIGN_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 600 I = 1, N
         R(I) = SIGN(X(I), Y(I))
600   CONTINUE

      RETURN
      END


      SUBROUTINE SIGN_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 610 I = 1, N
         R(I) = DSIGN(X(I), Y(I))
610   CONTINUE

      RETURN
      END


      SUBROUTINE MOD_I4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      INTEGER, CONTIGUOUS :: Y(:)
      INTEGER, CONTIGUOUS :: R(:)

      DO 620 I = 1, N
         R(I) = MOD(X(I), Y(I))
620   CONTINUE

      RETURN
      END


      SUBROUTINE MOD_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 630 I = 1, N
         R(I) = AMOD(X(I), Y(I))
630   CONTINUE

      RETURN
      END


      SUBROUTINE MOD_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 640 I = 1, N
         R(I) = DMOD(X(I), Y(I))
640   CONTINUE

      RETURN
      END


      SUBROUTINE DEG2RAD_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)
      REAL PI

      PI = 3.14159265358979323846

      DO 650 I = 1, N
         R(I) = X(I) * PI / 180.0
650   CONTINUE

      RETURN
      END


      SUBROUTINE DEG2RAD_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)
      DOUBLE PRECISION PI

      PI = 3.1415926535897932384626433832795D0

      DO 660 I = 1, N
         R(I) = X(I) * PI / 180.0D0
660   CONTINUE

      RETURN
      END


      SUBROUTINE RAD2DEG_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: R(:)
      REAL PI

      PI = 3.14159265358979323846

      DO 670 I = 1, N
         R(I) = X(I) * 180.0 / PI
670   CONTINUE

      RETURN
      END


      SUBROUTINE RAD2DEG_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)
      DOUBLE PRECISION PI

      PI = 3.1415926535897932384626433832795D0

      DO 680 I = 1, N
         R(I) = X(I) * 180.0D0 / PI
680   CONTINUE

      RETURN
      END


      SUBROUTINE DIST2_R4_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      REAL, CONTIGUOUS :: Y(:)
      REAL, CONTIGUOUS :: R(:)

      DO 690 I = 1, N
         R(I) = X(I) * X(I) + Y(I) * Y(I)
690   CONTINUE

      RETURN
      END


      SUBROUTINE DIST2_R8_CONTIGUOUS(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 700 I = 1, N
         R(I) = X(I) * X(I) + Y(I) * Y(I)
700   CONTINUE

      RETURN
      END


      SUBROUTINE DOT2_R4_CONTIGUOUS(N, X1, X2, Y1, Y2, R)
      INTEGER N
      REAL, CONTIGUOUS :: X1(:)
      REAL, CONTIGUOUS :: X2(:)
      REAL, CONTIGUOUS :: Y1(:)
      REAL, CONTIGUOUS :: Y2(:)
      REAL, CONTIGUOUS :: R(:)

      DO 710 I = 1, N
         R(I) = X1(I) * Y1(I) + X2(I) * Y2(I)
710   CONTINUE

      RETURN
      END


      SUBROUTINE DOT2_R8_CONTIGUOUS(N, X1, X2, Y1, Y2, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X1(:)
      DOUBLE PRECISION, CONTIGUOUS :: X2(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y1(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y2(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 720 I = 1, N
         R(I) = X1(I) * Y1(I) + X2(I) * Y2(I)
720   CONTINUE

      RETURN
      END


      SUBROUTINE DOT3_R4_CONTIGUOUS(N, X1, X2, X3, Y1, Y2, Y3, R)
      INTEGER N
      REAL, CONTIGUOUS :: X1(:)
      REAL, CONTIGUOUS :: X2(:)
      REAL, CONTIGUOUS :: X3(:)
      REAL, CONTIGUOUS :: Y1(:)
      REAL, CONTIGUOUS :: Y2(:)
      REAL, CONTIGUOUS :: Y3(:)
      REAL, CONTIGUOUS :: R(:)

      DO 730 I = 1, N
         R(I) = X1(I) * Y1(I)
         R(I) = R(I) + X2(I) * Y2(I)
         R(I) = R(I) + X3(I) * Y3(I)
730   CONTINUE

      RETURN
      END


      SUBROUTINE DOT3_R8_CONTIGUOUS(N, X1, X2, X3, Y1, Y2, Y3, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X1(:)
      DOUBLE PRECISION, CONTIGUOUS :: X2(:)
      DOUBLE PRECISION, CONTIGUOUS :: X3(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y1(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y2(:)
      DOUBLE PRECISION, CONTIGUOUS :: Y3(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 740 I = 1, N
         R(I) = X1(I) * Y1(I)
         R(I) = R(I) + X2(I) * Y2(I)
         R(I) = R(I) + X3(I) * Y3(I)
740   CONTINUE

      RETURN
      END


      SUBROUTINE CONJ_C4_CONTIGUOUS(N, Z, R)
      INTEGER N
      COMPLEX, CONTIGUOUS :: Z(:)
      COMPLEX, CONTIGUOUS :: R(:)

      DO 750 I = 1, N
         R(I) = CONJG(Z(I))
750   CONTINUE

      RETURN
      END


      SUBROUTINE CONJ_C8_CONTIGUOUS(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX, CONTIGUOUS :: Z(:)
      DOUBLE COMPLEX, CONTIGUOUS :: R(:)

      DO 760 I = 1, N
         R(I) = DCONJG(Z(I))
760   CONTINUE

      RETURN
      END


      SUBROUTINE REAL_C4_CONTIGUOUS(N, Z, R)
      INTEGER N
      COMPLEX, CONTIGUOUS :: Z(:)
      REAL, CONTIGUOUS :: R(:)

      DO 770 I = 1, N
         R(I) = REAL(Z(I))
770   CONTINUE

      RETURN
      END


      SUBROUTINE REAL_C8_CONTIGUOUS(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX, CONTIGUOUS :: Z(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 780 I = 1, N
         R(I) = DBLE(Z(I))
780   CONTINUE

      RETURN
      END


      SUBROUTINE AIMAG_C4_CONTIGUOUS(N, Z, R)
      INTEGER N
      COMPLEX, CONTIGUOUS :: Z(:)
      REAL, CONTIGUOUS :: R(:)

      DO 790 I = 1, N
         R(I) = AIMAG(Z(I))
790   CONTINUE

      RETURN
      END


      SUBROUTINE AIMAG_C8_CONTIGUOUS(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX, CONTIGUOUS :: Z(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 800 I = 1, N
         R(I) = DIMAG(Z(I))
800   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_C4_CONTIGUOUS(N, Z, R)
      INTEGER N
      COMPLEX, CONTIGUOUS :: Z(:)
      REAL, CONTIGUOUS :: R(:)

      DO 810 I = 1, N
         R(I) = ABS(Z(I))
810   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_C8_CONTIGUOUS(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX, CONTIGUOUS :: Z(:)
      DOUBLE PRECISION, CONTIGUOUS :: R(:)

      DO 820 I = 1, N
         R(I) = CDABS(Z(I))
820   CONTINUE

      RETURN
      END


      SUBROUTINE IS_POSITIVE_R4_CONTIGUOUS(N, X, R)
      INTEGER N
      REAL, CONTIGUOUS :: X(:)
      LOGICAL(1), CONTIGUOUS :: R(:)

      DO 830 I = 1, N
         R(I) = X(I) .GT. 0.0
830   CONTINUE

      RETURN
      END


      SUBROUTINE IS_POSITIVE_R8_CONTIGUOUS(N, X, R)
      INTEGER N
      DOUBLE PRECISION, CONTIGUOUS :: X(:)
      LOGICAL(1), CONTIGUOUS :: R(:)

      DO 840 I = 1, N
         R(I) = X(I) .GT. 0.0D0
840   CONTINUE

      RETURN
      END


      SUBROUTINE IS_EVEN_I4_CONTIGUOUS(N, X, R)
      INTEGER N
      INTEGER, CONTIGUOUS :: X(:)
      LOGICAL(1), CONTIGUOUS :: R(:)

      DO 850 I = 1, N
         R(I) = MOD(X(I), 2) .EQ. 0
850   CONTINUE

      RETURN
      END

      SUBROUTINE SQUARE_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 10 I = 1, N
         R(I) = X(I) * X(I)
10    CONTINUE

      RETURN
      END


      SUBROUTINE SQUARE_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 20 I = 1, N
         R(I) = X(I) * X(I)
20    CONTINUE

      RETURN
      END


      SUBROUTINE SQUARE_I4_STRIDED(N, X, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: R(:)

      DO 30 I = 1, N
         R(I) = X(I) * X(I)
30    CONTINUE

      RETURN
      END


      SUBROUTINE SQUARE_C4_STRIDED(N, Z, R)
      INTEGER N
      COMPLEX :: Z(:)
      COMPLEX :: R(:)

      DO 40 I = 1, N
         R(I) = Z(I) * Z(I)
40    CONTINUE

      RETURN
      END


      SUBROUTINE SQUARE_C8_STRIDED(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX :: Z(:)
      DOUBLE COMPLEX :: R(:)

      DO 50 I = 1, N
         R(I) = Z(I) * Z(I)
50    CONTINUE

      RETURN
      END


      SUBROUTINE CUBE_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 60 I = 1, N
         R(I) = X(I) * X(I) * X(I)
60    CONTINUE

      RETURN
      END


      SUBROUTINE CUBE_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 70 I = 1, N
         R(I) = X(I) * X(I) * X(I)
70    CONTINUE

      RETURN
      END


      SUBROUTINE CUBE_I4_STRIDED(N, X, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: R(:)

      DO 80 I = 1, N
         R(I) = X(I) * X(I) * X(I)
80    CONTINUE

      RETURN
      END


      SUBROUTINE ADD_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 90 I = 1, N
         R(I) = X(I) + Y(I)
90    CONTINUE

      RETURN
      END


      SUBROUTINE ADD_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 100 I = 1, N
         R(I) = X(I) + Y(I)
100   CONTINUE

      RETURN
      END


      SUBROUTINE ADD_I4_STRIDED(N, X, Y, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: Y(:)
      INTEGER :: R(:)

      DO 110 I = 1, N
         R(I) = X(I) + Y(I)
110   CONTINUE

      RETURN
      END


      SUBROUTINE ADD_C4_STRIDED(N, X, Y, R)
      INTEGER N
      COMPLEX :: X(:)
      COMPLEX :: Y(:)
      COMPLEX :: R(:)

      DO 120 I = 1, N
         R(I) = X(I) + Y(I)
120   CONTINUE

      RETURN
      END


      SUBROUTINE ADD_C8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE COMPLEX :: X(:)
      DOUBLE COMPLEX :: Y(:)
      DOUBLE COMPLEX :: R(:)

      DO 130 I = 1, N
         R(I) = X(I) + Y(I)
130   CONTINUE

      RETURN
      END


      SUBROUTINE SUB_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 140 I = 1, N
         R(I) = X(I) - Y(I)
140   CONTINUE

      RETURN
      END


      SUBROUTINE SUB_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 150 I = 1, N
         R(I) = X(I) - Y(I)
150   CONTINUE

      RETURN
      END


      SUBROUTINE SUB_I4_STRIDED(N, X, Y, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: Y(:)
      INTEGER :: R(:)

      DO 160 I = 1, N
         R(I) = X(I) - Y(I)
160   CONTINUE

      RETURN
      END


      SUBROUTINE MUL_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 170 I = 1, N
         R(I) = X(I) * Y(I)
170   CONTINUE

      RETURN
      END


      SUBROUTINE MUL_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 180 I = 1, N
         R(I) = X(I) * Y(I)
180   CONTINUE

      RETURN
      END


      SUBROUTINE MUL_I4_STRIDED(N, X, Y, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: Y(:)
      INTEGER :: R(:)

      DO 190 I = 1, N
         R(I) = X(I) * Y(I)
190   CONTINUE

      RETURN
      END


      SUBROUTINE DIV_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 200 I = 1, N
         R(I) = X(I) / Y(I)
200   CONTINUE

      RETURN
      END


      SUBROUTINE DIV_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 210 I = 1, N
         R(I) = X(I) / Y(I)
210   CONTINUE

      RETURN
      END


      SUBROUTINE POW_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 220 I = 1, N
         R(I) = X(I) ** Y(I)
220   CONTINUE

      RETURN
      END


      SUBROUTINE POW_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 230 I = 1, N
         R(I) = X(I) ** Y(I)
230   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 240 I = 1, N
         R(I) = ABS(X(I))
240   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 250 I = 1, N
         R(I) = ABS(X(I))
250   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_I4_STRIDED(N, X, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: R(:)

      DO 260 I = 1, N
         R(I) = ABS(X(I))
260   CONTINUE

      RETURN
      END


      SUBROUTINE NEG_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 270 I = 1, N
         R(I) = -X(I)
270   CONTINUE

      RETURN
      END


      SUBROUTINE NEG_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 280 I = 1, N
         R(I) = -X(I)
280   CONTINUE

      RETURN
      END


      SUBROUTINE NEG_I4_STRIDED(N, X, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: R(:)

      DO 290 I = 1, N
         R(I) = -X(I)
290   CONTINUE

      RETURN
      END


      SUBROUTINE SIN_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 300 I = 1, N
         R(I) = SIN(X(I))
300   CONTINUE

      RETURN
      END


      SUBROUTINE SIN_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 310 I = 1, N
         R(I) = DSIN(X(I))
310   CONTINUE

      RETURN
      END


      SUBROUTINE COS_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 320 I = 1, N
         R(I) = COS(X(I))
320   CONTINUE

      RETURN
      END


      SUBROUTINE COS_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 330 I = 1, N
         R(I) = DCOS(X(I))
330   CONTINUE

      RETURN
      END


      SUBROUTINE TAN_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 340 I = 1, N
         R(I) = TAN(X(I))
340   CONTINUE

      RETURN
      END


      SUBROUTINE TAN_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 350 I = 1, N
         R(I) = DTAN(X(I))
350   CONTINUE

      RETURN
      END


      SUBROUTINE ASIN_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 360 I = 1, N
         R(I) = ASIN(X(I))
360   CONTINUE

      RETURN
      END


      SUBROUTINE ASIN_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 370 I = 1, N
         R(I) = DASIN(X(I))
370   CONTINUE

      RETURN
      END


      SUBROUTINE ACOS_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 380 I = 1, N
         R(I) = ACOS(X(I))
380   CONTINUE

      RETURN
      END


      SUBROUTINE ACOS_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 390 I = 1, N
         R(I) = DACOS(X(I))
390   CONTINUE

      RETURN
      END


      SUBROUTINE ATAN_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 400 I = 1, N
         R(I) = ATAN(X(I))
400   CONTINUE

      RETURN
      END


      SUBROUTINE ATAN_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 410 I = 1, N
         R(I) = DATAN(X(I))
410   CONTINUE

      RETURN
      END


      SUBROUTINE ATAN2_R4_STRIDED(N, Y, X, R)
      INTEGER N
      REAL :: Y(:)
      REAL :: X(:)
      REAL :: R(:)

      DO 420 I = 1, N
         R(I) = ATAN2(Y(I), X(I))
420   CONTINUE

      RETURN
      END


      SUBROUTINE ATAN2_R8_STRIDED(N, Y, X, R)
      INTEGER N
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 430 I = 1, N
         R(I) = DATAN2(Y(I), X(I))
430   CONTINUE

      RETURN
      END


      SUBROUTINE EXP_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 440 I = 1, N
         R(I) = EXP(X(I))
440   CONTINUE

      RETURN
      END


      SUBROUTINE EXP_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 450 I = 1, N
         R(I) = DEXP(X(I))
450   CONTINUE

      RETURN
      END


      SUBROUTINE LOG_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 460 I = 1, N
         R(I) = LOG(X(I))
460   CONTINUE

      RETURN
      END


      SUBROUTINE LOG_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 470 I = 1, N
         R(I) = DLOG(X(I))
470   CONTINUE

      RETURN
      END


      SUBROUTINE LOG10_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 480 I = 1, N
         R(I) = LOG10(X(I))
480   CONTINUE

      RETURN
      END


      SUBROUTINE LOG10_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 490 I = 1, N
         R(I) = DLOG10(X(I))
490   CONTINUE

      RETURN
      END


      SUBROUTINE SQRT_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)

      DO 500 I = 1, N
         R(I) = SQRT(X(I))
500   CONTINUE

      RETURN
      END


      SUBROUTINE SQRT_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)

      DO 510 I = 1, N
         R(I) = DSQRT(X(I))
510   CONTINUE

      RETURN
      END


      SUBROUTINE HYPOT_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 520 I = 1, N
         R(I) = SQRT(X(I) * X(I) + Y(I) * Y(I))
520   CONTINUE

      RETURN
      END


      SUBROUTINE HYPOT_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 530 I = 1, N
         R(I) = DSQRT(X(I) * X(I) + Y(I) * Y(I))
530   CONTINUE

      RETURN
      END


      SUBROUTINE MIN_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 540 I = 1, N
         R(I) = MIN(X(I), Y(I))
540   CONTINUE

      RETURN
      END


      SUBROUTINE MIN_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 550 I = 1, N
         R(I) = DMIN1(X(I), Y(I))
550   CONTINUE

      RETURN
      END


      SUBROUTINE MIN_I4_STRIDED(N, X, Y, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: Y(:)
      INTEGER :: R(:)

      DO 560 I = 1, N
         R(I) = MIN(X(I), Y(I))
560   CONTINUE

      RETURN
      END


      SUBROUTINE MAX_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 570 I = 1, N
         R(I) = MAX(X(I), Y(I))
570   CONTINUE

      RETURN
      END


      SUBROUTINE MAX_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 580 I = 1, N
         R(I) = DMAX1(X(I), Y(I))
580   CONTINUE

      RETURN
      END


      SUBROUTINE MAX_I4_STRIDED(N, X, Y, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: Y(:)
      INTEGER :: R(:)

      DO 590 I = 1, N
         R(I) = MAX(X(I), Y(I))
590   CONTINUE

      RETURN
      END


      SUBROUTINE SIGN_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 600 I = 1, N
         R(I) = SIGN(X(I), Y(I))
600   CONTINUE

      RETURN
      END


      SUBROUTINE SIGN_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 610 I = 1, N
         R(I) = DSIGN(X(I), Y(I))
610   CONTINUE

      RETURN
      END


      SUBROUTINE MOD_I4_STRIDED(N, X, Y, R)
      INTEGER N
      INTEGER :: X(:)
      INTEGER :: Y(:)
      INTEGER :: R(:)

      DO 620 I = 1, N
         R(I) = MOD(X(I), Y(I))
620   CONTINUE

      RETURN
      END


      SUBROUTINE MOD_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 630 I = 1, N
         R(I) = AMOD(X(I), Y(I))
630   CONTINUE

      RETURN
      END


      SUBROUTINE MOD_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 640 I = 1, N
         R(I) = DMOD(X(I), Y(I))
640   CONTINUE

      RETURN
      END


      SUBROUTINE DEG2RAD_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)
      REAL PI

      PI = 3.14159265358979323846

      DO 650 I = 1, N
         R(I) = X(I) * PI / 180.0
650   CONTINUE

      RETURN
      END


      SUBROUTINE DEG2RAD_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)
      DOUBLE PRECISION PI

      PI = 3.1415926535897932384626433832795D0

      DO 660 I = 1, N
         R(I) = X(I) * PI / 180.0D0
660   CONTINUE

      RETURN
      END


      SUBROUTINE RAD2DEG_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      REAL :: R(:)
      REAL PI

      PI = 3.14159265358979323846

      DO 670 I = 1, N
         R(I) = X(I) * 180.0 / PI
670   CONTINUE

      RETURN
      END


      SUBROUTINE RAD2DEG_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: R(:)
      DOUBLE PRECISION PI

      PI = 3.1415926535897932384626433832795D0

      DO 680 I = 1, N
         R(I) = X(I) * 180.0D0 / PI
680   CONTINUE

      RETURN
      END


      SUBROUTINE DIST2_R4_STRIDED(N, X, Y, R)
      INTEGER N
      REAL :: X(:)
      REAL :: Y(:)
      REAL :: R(:)

      DO 690 I = 1, N
         R(I) = X(I) * X(I) + Y(I) * Y(I)
690   CONTINUE

      RETURN
      END


      SUBROUTINE DIST2_R8_STRIDED(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      DOUBLE PRECISION :: Y(:)
      DOUBLE PRECISION :: R(:)

      DO 700 I = 1, N
         R(I) = X(I) * X(I) + Y(I) * Y(I)
700   CONTINUE

      RETURN
      END


      SUBROUTINE DOT2_R4_STRIDED(N, X1, X2, Y1, Y2, R)
      INTEGER N
      REAL :: X1(:)
      REAL :: X2(:)
      REAL :: Y1(:)
      REAL :: Y2(:)
      REAL :: R(:)

      DO 710 I = 1, N
         R(I) = X1(I) * Y1(I) + X2(I) * Y2(I)
710   CONTINUE

      RETURN
      END


      SUBROUTINE DOT2_R8_STRIDED(N, X1, X2, Y1, Y2, R)
      INTEGER N
      DOUBLE PRECISION :: X1(:)
      DOUBLE PRECISION :: X2(:)
      DOUBLE PRECISION :: Y1(:)
      DOUBLE PRECISION :: Y2(:)
      DOUBLE PRECISION :: R(:)

      DO 720 I = 1, N
         R(I) = X1(I) * Y1(I) + X2(I) * Y2(I)
720   CONTINUE

      RETURN
      END


      SUBROUTINE DOT3_R4_STRIDED(N, X1, X2, X3, Y1, Y2, Y3, R)
      INTEGER N
      REAL :: X1(:)
      REAL :: X2(:)
      REAL :: X3(:)
      REAL :: Y1(:)
      REAL :: Y2(:)
      REAL :: Y3(:)
      REAL :: R(:)

      DO 730 I = 1, N
         R(I) = X1(I) * Y1(I)
         R(I) = R(I) + X2(I) * Y2(I)
         R(I) = R(I) + X3(I) * Y3(I)
730   CONTINUE

      RETURN
      END


      SUBROUTINE DOT3_R8_STRIDED(N, X1, X2, X3, Y1, Y2, Y3, R)
      INTEGER N
      DOUBLE PRECISION :: X1(:)
      DOUBLE PRECISION :: X2(:)
      DOUBLE PRECISION :: X3(:)
      DOUBLE PRECISION :: Y1(:)
      DOUBLE PRECISION :: Y2(:)
      DOUBLE PRECISION :: Y3(:)
      DOUBLE PRECISION :: R(:)

      DO 740 I = 1, N
         R(I) = X1(I) * Y1(I)
         R(I) = R(I) + X2(I) * Y2(I)
         R(I) = R(I) + X3(I) * Y3(I)
740   CONTINUE

      RETURN
      END


      SUBROUTINE CONJ_C4_STRIDED(N, Z, R)
      INTEGER N
      COMPLEX :: Z(:)
      COMPLEX :: R(:)

      DO 750 I = 1, N
         R(I) = CONJG(Z(I))
750   CONTINUE

      RETURN
      END


      SUBROUTINE CONJ_C8_STRIDED(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX :: Z(:)
      DOUBLE COMPLEX :: R(:)

      DO 760 I = 1, N
         R(I) = DCONJG(Z(I))
760   CONTINUE

      RETURN
      END


      SUBROUTINE REAL_C4_STRIDED(N, Z, R)
      INTEGER N
      COMPLEX :: Z(:)
      REAL :: R(:)

      DO 770 I = 1, N
         R(I) = REAL(Z(I))
770   CONTINUE

      RETURN
      END


      SUBROUTINE REAL_C8_STRIDED(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX :: Z(:)
      DOUBLE PRECISION :: R(:)

      DO 780 I = 1, N
         R(I) = DBLE(Z(I))
780   CONTINUE

      RETURN
      END


      SUBROUTINE AIMAG_C4_STRIDED(N, Z, R)
      INTEGER N
      COMPLEX :: Z(:)
      REAL :: R(:)

      DO 790 I = 1, N
         R(I) = AIMAG(Z(I))
790   CONTINUE

      RETURN
      END


      SUBROUTINE AIMAG_C8_STRIDED(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX :: Z(:)
      DOUBLE PRECISION :: R(:)

      DO 800 I = 1, N
         R(I) = DIMAG(Z(I))
800   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_C4_STRIDED(N, Z, R)
      INTEGER N
      COMPLEX :: Z(:)
      REAL :: R(:)

      DO 810 I = 1, N
         R(I) = ABS(Z(I))
810   CONTINUE

      RETURN
      END


      SUBROUTINE ABS_C8_STRIDED(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX :: Z(:)
      DOUBLE PRECISION :: R(:)

      DO 820 I = 1, N
         R(I) = CDABS(Z(I))
820   CONTINUE

      RETURN
      END


      SUBROUTINE IS_POSITIVE_R4_STRIDED(N, X, R)
      INTEGER N
      REAL :: X(:)
      LOGICAL(1) :: R(:)

      DO 830 I = 1, N
         R(I) = X(I) .GT. 0.0
830   CONTINUE

      RETURN
      END


      SUBROUTINE IS_POSITIVE_R8_STRIDED(N, X, R)
      INTEGER N
      DOUBLE PRECISION :: X(:)
      LOGICAL(1) :: R(:)

      DO 840 I = 1, N
         R(I) = X(I) .GT. 0.0D0
840   CONTINUE

      RETURN
      END


      SUBROUTINE IS_EVEN_I4_STRIDED(N, X, R)
      INTEGER N
      INTEGER :: X(:)
      LOGICAL(1) :: R(:)

      DO 850 I = 1, N
         R(I) = MOD(X(I), 2) .EQ. 0
850   CONTINUE

      RETURN
      END

end module fmath_arrays_f90
