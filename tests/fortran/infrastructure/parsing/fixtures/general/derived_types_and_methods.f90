module mesh_mod
  type :: node
    integer :: id
    real(kind=8), dimension(3) :: xyz
  contains
    procedure :: move
  end type node

  type :: mesh
    integer :: nnodes
    type(node), allocatable :: nodes(:)
  contains
    procedure :: init, clear
  end type mesh
end module mesh_mod
