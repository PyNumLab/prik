subroutine fill_grid(x)
  integer, intent(inout) :: x(0:,0:)
end subroutine fill_grid

subroutine update_plane(x)
  real, intent(inout), dimension(0:, 1:n) :: x
  integer, intent(in) :: n
end subroutine update_plane

subroutine step(state)
  type(sim_state), intent(inout) :: state
end subroutine step
