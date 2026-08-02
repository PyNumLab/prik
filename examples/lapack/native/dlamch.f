      DOUBLE PRECISION FUNCTION DLAMCH( CMACH )
      CHARACTER          CMACH
      DOUBLE PRECISION   EPS, SFMIN, BASE, PREC, RND, TINYVAL, HUGEVAL
      INTEGER            NDIG, MINEXP, MAXEXP
      EPS = EPSILON( 0.0D0 )
      BASE = DBLE( RADIX( 0.0D0 ) )
      NDIG = DIGITS( 0.0D0 )
      MINEXP = MINEXPONENT( 0.0D0 )
      MAXEXP = MAXEXPONENT( 0.0D0 )
      TINYVAL = TINY( 0.0D0 )
      HUGEVAL = HUGE( 0.0D0 )
      SFMIN = TINYVAL
      PREC = EPS * BASE
      RND = 1.0D0
      IF ( CMACH .EQ. 'E' .OR. CMACH .EQ. 'e' ) THEN
         DLAMCH = EPS
      ELSE IF ( CMACH .EQ. 'S' .OR. CMACH .EQ. 's' ) THEN
         DLAMCH = SFMIN
      ELSE IF ( CMACH .EQ. 'B' .OR. CMACH .EQ. 'b' ) THEN
         DLAMCH = BASE
      ELSE IF ( CMACH .EQ. 'P' .OR. CMACH .EQ. 'p' ) THEN
         DLAMCH = PREC
      ELSE IF ( CMACH .EQ. 'N' .OR. CMACH .EQ. 'n' ) THEN
         DLAMCH = DBLE( NDIG )
      ELSE IF ( CMACH .EQ. 'R' .OR. CMACH .EQ. 'r' ) THEN
         DLAMCH = RND
      ELSE IF ( CMACH .EQ. 'M' .OR. CMACH .EQ. 'm' ) THEN
         DLAMCH = DBLE( MINEXP )
      ELSE IF ( CMACH .EQ. 'U' .OR. CMACH .EQ. 'u' ) THEN
         DLAMCH = TINYVAL
      ELSE IF ( CMACH .EQ. 'L' .OR. CMACH .EQ. 'l' ) THEN
         DLAMCH = DBLE( MAXEXP )
      ELSE IF ( CMACH .EQ. 'O' .OR. CMACH .EQ. 'o' ) THEN
         DLAMCH = HUGEVAL
      ELSE
         DLAMCH = 0.0D0
      END IF
      RETURN
      END
