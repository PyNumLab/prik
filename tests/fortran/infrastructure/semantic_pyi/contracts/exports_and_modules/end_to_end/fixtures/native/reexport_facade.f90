module alias_facade
  use alias_home, only : lambda => target
  implicit none
  public :: lambda

contains

  subroutine lambda_()
  end subroutine lambda_
end module alias_facade
