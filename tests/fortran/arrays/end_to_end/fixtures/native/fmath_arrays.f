      SUBROUTINE SQUARE_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 10 I = 1, N
         R(I) = X(I) * X(I)
10    CONTINUE

      RETURN
      END

      SUBROUTINE SQUARE_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 20 I = 1, N
         R(I) = X(I) * X(I)
20    CONTINUE

      RETURN
      END

      SUBROUTINE SQUARE_I4(N, X, R)
      INTEGER N
      INTEGER X(N)
      INTEGER R(N)

      DO 30 I = 1, N
         R(I) = X(I) * X(I)
30    CONTINUE

      RETURN
      END

      SUBROUTINE SQUARE_C4(N, Z, R)
      INTEGER N
      COMPLEX Z(N)
      COMPLEX R(N)

      DO 40 I = 1, N
         R(I) = Z(I) * Z(I)
40    CONTINUE

      RETURN
      END

      SUBROUTINE SQUARE_C8(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX Z(N)
      DOUBLE COMPLEX R(N)

      DO 50 I = 1, N
         R(I) = Z(I) * Z(I)
50    CONTINUE

      RETURN
      END

      SUBROUTINE CUBE_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 60 I = 1, N
         R(I) = X(I) * X(I) * X(I)
60    CONTINUE

      RETURN
      END

      SUBROUTINE CUBE_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 70 I = 1, N
         R(I) = X(I) * X(I) * X(I)
70    CONTINUE

      RETURN
      END

      SUBROUTINE CUBE_I4(N, X, R)
      INTEGER N
      INTEGER X(N)
      INTEGER R(N)

      DO 80 I = 1, N
         R(I) = X(I) * X(I) * X(I)
80    CONTINUE

      RETURN
      END

      SUBROUTINE ADD_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 90 I = 1, N
         R(I) = X(I) + Y(I)
90    CONTINUE

      RETURN
      END

      SUBROUTINE ADD_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 100 I = 1, N
         R(I) = X(I) + Y(I)
100   CONTINUE

      RETURN
      END

      SUBROUTINE ADD_I4(N, X, Y, R)
      INTEGER N
      INTEGER X(N)
      INTEGER Y(N)
      INTEGER R(N)

      DO 110 I = 1, N
         R(I) = X(I) + Y(I)
110   CONTINUE

      RETURN
      END

      SUBROUTINE ADD_C4(N, X, Y, R)
      INTEGER N
      COMPLEX X(N)
      COMPLEX Y(N)
      COMPLEX R(N)

      DO 120 I = 1, N
         R(I) = X(I) + Y(I)
120   CONTINUE

      RETURN
      END

      SUBROUTINE ADD_C8(N, X, Y, R)
      INTEGER N
      DOUBLE COMPLEX X(N)
      DOUBLE COMPLEX Y(N)
      DOUBLE COMPLEX R(N)

      DO 130 I = 1, N
         R(I) = X(I) + Y(I)
130   CONTINUE

      RETURN
      END

      SUBROUTINE SUB_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 140 I = 1, N
         R(I) = X(I) - Y(I)
140   CONTINUE

      RETURN
      END

      SUBROUTINE SUB_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 150 I = 1, N
         R(I) = X(I) - Y(I)
150   CONTINUE

      RETURN
      END

      SUBROUTINE SUB_I4(N, X, Y, R)
      INTEGER N
      INTEGER X(N)
      INTEGER Y(N)
      INTEGER R(N)

      DO 160 I = 1, N
         R(I) = X(I) - Y(I)
160   CONTINUE

      RETURN
      END

      SUBROUTINE MUL_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 170 I = 1, N
         R(I) = X(I) * Y(I)
170   CONTINUE

      RETURN
      END

      SUBROUTINE MUL_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 180 I = 1, N
         R(I) = X(I) * Y(I)
180   CONTINUE

      RETURN
      END

      SUBROUTINE MUL_I4(N, X, Y, R)
      INTEGER N
      INTEGER X(N)
      INTEGER Y(N)
      INTEGER R(N)

      DO 190 I = 1, N
         R(I) = X(I) * Y(I)
190   CONTINUE

      RETURN
      END

      SUBROUTINE DIV_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 200 I = 1, N
         R(I) = X(I) / Y(I)
200   CONTINUE

      RETURN
      END

      SUBROUTINE DIV_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 210 I = 1, N
         R(I) = X(I) / Y(I)
210   CONTINUE

      RETURN
      END

      SUBROUTINE POW_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 220 I = 1, N
         R(I) = X(I) ** Y(I)
220   CONTINUE

      RETURN
      END

      SUBROUTINE POW_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 230 I = 1, N
         R(I) = X(I) ** Y(I)
230   CONTINUE

      RETURN
      END

      SUBROUTINE ABS_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 240 I = 1, N
         R(I) = ABS(X(I))
240   CONTINUE

      RETURN
      END

      SUBROUTINE ABS_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 250 I = 1, N
         R(I) = ABS(X(I))
250   CONTINUE

      RETURN
      END

      SUBROUTINE ABS_I4(N, X, R)
      INTEGER N
      INTEGER X(N)
      INTEGER R(N)

      DO 260 I = 1, N
         R(I) = ABS(X(I))
260   CONTINUE

      RETURN
      END

      SUBROUTINE NEG_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 270 I = 1, N
         R(I) = -X(I)
270   CONTINUE

      RETURN
      END

      SUBROUTINE NEG_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 280 I = 1, N
         R(I) = -X(I)
280   CONTINUE

      RETURN
      END

      SUBROUTINE NEG_I4(N, X, R)
      INTEGER N
      INTEGER X(N)
      INTEGER R(N)

      DO 290 I = 1, N
         R(I) = -X(I)
290   CONTINUE

      RETURN
      END

      SUBROUTINE SIN_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 300 I = 1, N
         R(I) = SIN(X(I))
300   CONTINUE

      RETURN
      END

      SUBROUTINE SIN_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 310 I = 1, N
         R(I) = DSIN(X(I))
310   CONTINUE

      RETURN
      END

      SUBROUTINE COS_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 320 I = 1, N
         R(I) = COS(X(I))
320   CONTINUE

      RETURN
      END

      SUBROUTINE COS_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 330 I = 1, N
         R(I) = DCOS(X(I))
330   CONTINUE

      RETURN
      END

      SUBROUTINE TAN_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 340 I = 1, N
         R(I) = TAN(X(I))
340   CONTINUE

      RETURN
      END

      SUBROUTINE TAN_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 350 I = 1, N
         R(I) = DTAN(X(I))
350   CONTINUE

      RETURN
      END

      SUBROUTINE ASIN_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 360 I = 1, N
         R(I) = ASIN(X(I))
360   CONTINUE

      RETURN
      END

      SUBROUTINE ASIN_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 370 I = 1, N
         R(I) = DASIN(X(I))
370   CONTINUE

      RETURN
      END

      SUBROUTINE ACOS_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 380 I = 1, N
         R(I) = ACOS(X(I))
380   CONTINUE

      RETURN
      END

      SUBROUTINE ACOS_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 390 I = 1, N
         R(I) = DACOS(X(I))
390   CONTINUE

      RETURN
      END

      SUBROUTINE ATAN_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 400 I = 1, N
         R(I) = ATAN(X(I))
400   CONTINUE

      RETURN
      END

      SUBROUTINE ATAN_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 410 I = 1, N
         R(I) = DATAN(X(I))
410   CONTINUE

      RETURN
      END

      SUBROUTINE ATAN2_R4(N, Y, X, R)
      INTEGER N
      REAL Y(N)
      REAL X(N)
      REAL R(N)

      DO 420 I = 1, N
         R(I) = ATAN2(Y(I), X(I))
420   CONTINUE

      RETURN
      END

      SUBROUTINE ATAN2_R8(N, Y, X, R)
      INTEGER N
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 430 I = 1, N
         R(I) = DATAN2(Y(I), X(I))
430   CONTINUE

      RETURN
      END

      SUBROUTINE EXP_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 440 I = 1, N
         R(I) = EXP(X(I))
440   CONTINUE

      RETURN
      END

      SUBROUTINE EXP_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 450 I = 1, N
         R(I) = DEXP(X(I))
450   CONTINUE

      RETURN
      END

      SUBROUTINE LOG_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 460 I = 1, N
         R(I) = LOG(X(I))
460   CONTINUE

      RETURN
      END

      SUBROUTINE LOG_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 470 I = 1, N
         R(I) = DLOG(X(I))
470   CONTINUE

      RETURN
      END

      SUBROUTINE LOG10_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 480 I = 1, N
         R(I) = LOG10(X(I))
480   CONTINUE

      RETURN
      END

      SUBROUTINE LOG10_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 490 I = 1, N
         R(I) = DLOG10(X(I))
490   CONTINUE

      RETURN
      END

      SUBROUTINE SQRT_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)

      DO 500 I = 1, N
         R(I) = SQRT(X(I))
500   CONTINUE

      RETURN
      END

      SUBROUTINE SQRT_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)

      DO 510 I = 1, N
         R(I) = DSQRT(X(I))
510   CONTINUE

      RETURN
      END

      SUBROUTINE HYPOT_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 520 I = 1, N
         R(I) = SQRT(X(I) * X(I) + Y(I) * Y(I))
520   CONTINUE

      RETURN
      END

      SUBROUTINE HYPOT_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 530 I = 1, N
         R(I) = DSQRT(X(I) * X(I) + Y(I) * Y(I))
530   CONTINUE

      RETURN
      END

      SUBROUTINE MIN_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 540 I = 1, N
         R(I) = MIN(X(I), Y(I))
540   CONTINUE

      RETURN
      END

      SUBROUTINE MIN_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 550 I = 1, N
         R(I) = DMIN1(X(I), Y(I))
550   CONTINUE

      RETURN
      END

      SUBROUTINE MIN_I4(N, X, Y, R)
      INTEGER N
      INTEGER X(N)
      INTEGER Y(N)
      INTEGER R(N)

      DO 560 I = 1, N
         R(I) = MIN(X(I), Y(I))
560   CONTINUE

      RETURN
      END

      SUBROUTINE MAX_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 570 I = 1, N
         R(I) = MAX(X(I), Y(I))
570   CONTINUE

      RETURN
      END

      SUBROUTINE MAX_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 580 I = 1, N
         R(I) = DMAX1(X(I), Y(I))
580   CONTINUE

      RETURN
      END

      SUBROUTINE MAX_I4(N, X, Y, R)
      INTEGER N
      INTEGER X(N)
      INTEGER Y(N)
      INTEGER R(N)

      DO 590 I = 1, N
         R(I) = MAX(X(I), Y(I))
590   CONTINUE

      RETURN
      END

      SUBROUTINE SIGN_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 600 I = 1, N
         R(I) = SIGN(X(I), Y(I))
600   CONTINUE

      RETURN
      END

      SUBROUTINE SIGN_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 610 I = 1, N
         R(I) = DSIGN(X(I), Y(I))
610   CONTINUE

      RETURN
      END

      SUBROUTINE MOD_I4(N, X, Y, R)
      INTEGER N
      INTEGER X(N)
      INTEGER Y(N)
      INTEGER R(N)

      DO 620 I = 1, N
         R(I) = MOD(X(I), Y(I))
620   CONTINUE

      RETURN
      END

      SUBROUTINE MOD_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 630 I = 1, N
         R(I) = AMOD(X(I), Y(I))
630   CONTINUE

      RETURN
      END

      SUBROUTINE MOD_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 640 I = 1, N
         R(I) = DMOD(X(I), Y(I))
640   CONTINUE

      RETURN
      END

      SUBROUTINE DEG2RAD_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)
      REAL PI

      PI = 3.14159265358979323846

      DO 650 I = 1, N
         R(I) = X(I) * PI / 180.0
650   CONTINUE

      RETURN
      END

      SUBROUTINE DEG2RAD_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)
      DOUBLE PRECISION PI

      PI = 3.1415926535897932384626433832795D0

      DO 660 I = 1, N
         R(I) = X(I) * PI / 180.0D0
660   CONTINUE

      RETURN
      END

      SUBROUTINE RAD2DEG_R4(N, X, R)
      INTEGER N
      REAL X(N)
      REAL R(N)
      REAL PI

      PI = 3.14159265358979323846

      DO 670 I = 1, N
         R(I) = X(I) * 180.0 / PI
670   CONTINUE

      RETURN
      END

      SUBROUTINE RAD2DEG_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION R(N)
      DOUBLE PRECISION PI

      PI = 3.1415926535897932384626433832795D0

      DO 680 I = 1, N
         R(I) = X(I) * 180.0D0 / PI
680   CONTINUE

      RETURN
      END

      SUBROUTINE DIST2_R4(N, X, Y, R)
      INTEGER N
      REAL X(N)
      REAL Y(N)
      REAL R(N)

      DO 690 I = 1, N
         R(I) = X(I) * X(I) + Y(I) * Y(I)
690   CONTINUE

      RETURN
      END

      SUBROUTINE DIST2_R8(N, X, Y, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      DOUBLE PRECISION Y(N)
      DOUBLE PRECISION R(N)

      DO 700 I = 1, N
         R(I) = X(I) * X(I) + Y(I) * Y(I)
700   CONTINUE

      RETURN
      END

      SUBROUTINE DOT2_R4(N, X1, X2, Y1, Y2, R)
      INTEGER N
      REAL X1(N)
      REAL X2(N)
      REAL Y1(N)
      REAL Y2(N)
      REAL R(N)

      DO 710 I = 1, N
         R(I) = X1(I) * Y1(I) + X2(I) * Y2(I)
710   CONTINUE

      RETURN
      END

      SUBROUTINE DOT2_R8(N, X1, X2, Y1, Y2, R)
      INTEGER N
      DOUBLE PRECISION X1(N)
      DOUBLE PRECISION X2(N)
      DOUBLE PRECISION Y1(N)
      DOUBLE PRECISION Y2(N)
      DOUBLE PRECISION R(N)

      DO 720 I = 1, N
         R(I) = X1(I) * Y1(I) + X2(I) * Y2(I)
720   CONTINUE

      RETURN
      END

      SUBROUTINE DOT3_R4(N, X1, X2, X3, Y1, Y2, Y3, R)
      INTEGER N
      REAL X1(N)
      REAL X2(N)
      REAL X3(N)
      REAL Y1(N)
      REAL Y2(N)
      REAL Y3(N)
      REAL R(N)

      DO 730 I = 1, N
         R(I) = X1(I) * Y1(I)
         R(I) = R(I) + X2(I) * Y2(I)
         R(I) = R(I) + X3(I) * Y3(I)
730   CONTINUE

      RETURN
      END

      SUBROUTINE DOT3_R8(N, X1, X2, X3, Y1, Y2, Y3, R)
      INTEGER N
      DOUBLE PRECISION X1(N)
      DOUBLE PRECISION X2(N)
      DOUBLE PRECISION X3(N)
      DOUBLE PRECISION Y1(N)
      DOUBLE PRECISION Y2(N)
      DOUBLE PRECISION Y3(N)
      DOUBLE PRECISION R(N)

      DO 740 I = 1, N
         R(I) = X1(I) * Y1(I)
         R(I) = R(I) + X2(I) * Y2(I)
         R(I) = R(I) + X3(I) * Y3(I)
740   CONTINUE

      RETURN
      END

      SUBROUTINE CONJ_C4(N, Z, R)
      INTEGER N
      COMPLEX Z(N)
      COMPLEX R(N)

      DO 750 I = 1, N
         R(I) = CONJG(Z(I))
750   CONTINUE

      RETURN
      END

      SUBROUTINE CONJ_C8(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX Z(N)
      DOUBLE COMPLEX R(N)

      DO 760 I = 1, N
         R(I) = DCONJG(Z(I))
760   CONTINUE

      RETURN
      END

      SUBROUTINE REAL_C4(N, Z, R)
      INTEGER N
      COMPLEX Z(N)
      REAL R(N)

      DO 770 I = 1, N
         R(I) = REAL(Z(I))
770   CONTINUE

      RETURN
      END

      SUBROUTINE REAL_C8(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX Z(N)
      DOUBLE PRECISION R(N)

      DO 780 I = 1, N
         R(I) = DBLE(Z(I))
780   CONTINUE

      RETURN
      END

      SUBROUTINE AIMAG_C4(N, Z, R)
      INTEGER N
      COMPLEX Z(N)
      REAL R(N)

      DO 790 I = 1, N
         R(I) = AIMAG(Z(I))
790   CONTINUE

      RETURN
      END

      SUBROUTINE AIMAG_C8(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX Z(N)
      DOUBLE PRECISION R(N)

      DO 800 I = 1, N
         R(I) = DIMAG(Z(I))
800   CONTINUE

      RETURN
      END

      SUBROUTINE ABS_C4(N, Z, R)
      INTEGER N
      COMPLEX Z(N)
      REAL R(N)

      DO 810 I = 1, N
         R(I) = ABS(Z(I))
810   CONTINUE

      RETURN
      END

      SUBROUTINE ABS_C8(N, Z, R)
      INTEGER N
      DOUBLE COMPLEX Z(N)
      DOUBLE PRECISION R(N)

      DO 820 I = 1, N
         R(I) = CDABS(Z(I))
820   CONTINUE

      RETURN
      END

      SUBROUTINE IS_POSITIVE_R4(N, X, R)
      INTEGER N
      REAL X(N)
      LOGICAL*1 R(N)

      DO 830 I = 1, N
         R(I) = X(I) .GT. 0.0
830   CONTINUE

      RETURN
      END

      SUBROUTINE IS_POSITIVE_R8(N, X, R)
      INTEGER N
      DOUBLE PRECISION X(N)
      LOGICAL*1 R(N)

      DO 840 I = 1, N
         R(I) = X(I) .GT. 0.0D0
840   CONTINUE

      RETURN
      END

      SUBROUTINE IS_EVEN_I4(N, X, R)
      INTEGER N
      INTEGER X(N)
      LOGICAL*1 R(N)

      DO 850 I = 1, N
         R(I) = MOD(X(I), 2) .EQ. 0
850   CONTINUE

      RETURN
      END
