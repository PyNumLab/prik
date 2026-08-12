module bind_c_refactoring_goldens_wrapper
  use iso_c_binding, only: &
    c_associated, &
    c_bool, &
    c_char, &
    c_double, &
    c_double_complex, &
    c_f_pointer, &
    c_float, &
    c_float_complex, &
    c_int8_t, &
    c_int16_t, &
    c_int, &
    c_int32_t, &
    c_int64_t, &
    c_loc, &
    c_null_char, &
    c_ptr, &
    c_null_ptr, &
    c_size_t, &
    c_sizeof, &
    c_funptr, &
    c_f_procpointer, &
    c_funloc
  use refactoring_goldens, only: &
    prik_type_holder_item => holder_item, &
    prik_type_vector => vector, &
    native_summarize => summarize, &
    native_make_values => make_values, &
    native_apply_callback => apply_callback, &
    native_split_value => split_value, &
    native_reset_allocatable_item => reset_allocatable_item, &
    native_shift_pointer_item => shift_pointer_item, &
    operator(+), &
    native__prik_overload_convert_0 => convert, &
    native__prik_overload_convert_1 => convert, &
    native_counter => counter, &
    native_workspace => workspace, &
    native_selected => selected, &
    native_active_vector => active_vector, &
    native_selected_vector => selected_vector
  implicit none
  type :: prik_holder_item_allocatable_holder
    type(prik_type_holder_item), allocatable :: value
  end type prik_holder_item_allocatable_holder
  type :: prik_vector_allocatable_holder
    type(prik_type_vector), allocatable :: value
  end type prik_vector_allocatable_holder
  type :: prik_holder_item_pointer_holder
    type(prik_type_holder_item), pointer :: value
  end type prik_holder_item_pointer_holder
  type :: prik_vector_pointer_holder
    type(prik_type_vector), pointer :: value
  end type prik_vector_pointer_holder
  abstract interface
    function prik_derived_consumer(address, context) bind(c) result(status)
      import :: c_ptr, c_int
      type(c_ptr), value :: address
      type(c_ptr), value :: context
      integer(c_int) :: status
    end function prik_derived_consumer
    function prik_derived_scoped(consumer, context) bind(c) result(status)
      import :: c_ptr, c_funptr, c_int
      type(c_funptr), value :: consumer
      type(c_ptr), value :: context
      integer(c_int) :: status
    end function prik_derived_scoped
    function prik_derived_checkout(holder) bind(c) result(status)
      import :: c_ptr, c_int
      type(c_ptr), intent(out) :: holder
      integer(c_int) :: status
    end function prik_derived_checkout
    function prik_derived_restore(holder) bind(c) result(status)
      import :: c_ptr, c_int
      type(c_ptr), value :: holder
      integer(c_int) :: status
    end function prik_derived_restore
  end interface
  abstract interface
    function prik_scalar_callback_299cdba6(value) result(prik_result)
      import :: c_double
      real(c_double), intent(in) :: value
      real(c_double) :: prik_result
    end function prik_scalar_callback_299cdba6
  end interface
  interface
    subroutine prik_workspace_descriptor_consumer(value, context) bind(c, name="prik_workspace_descriptor_consumer")
      import :: c_double, c_ptr
      real(c_double), allocatable, dimension(:), intent(in) :: value
      type(c_ptr), value :: context
    end subroutine prik_workspace_descriptor_consumer
  end interface
  interface
    subroutine prik_field_handle_vector_samples_consumer(&
      & value, &
      & context) bind(c, name="prik_field_handle_vector_samples_consumer")
      import :: c_double, c_ptr
      real(c_double), allocatable, dimension(:), intent(in) :: value
      type(c_ptr), value :: context
    end subroutine prik_field_handle_vector_samples_consumer
    subroutine prik_module_field_handle_active_vector_samples_consumer(&
      & value, &
      & context) bind(c, name="prik_module_field_handle_active_vector_samples_consumer")
      import :: c_double, c_ptr
      real(c_double), allocatable, dimension(:), intent(in) :: value
      type(c_ptr), value :: context
    end subroutine prik_module_field_handle_active_vector_samples_consumer
    subroutine prik_module_field_handle_selected_vector_samples_consumer(&
      & value, &
      & context) bind(c, name="prik_module_field_handle_selected_vector_samples_consumer")
      import :: c_double, c_ptr
      real(c_double), allocatable, dimension(:), intent(in) :: value
      type(c_ptr), value :: context
    end subroutine prik_module_field_handle_selected_vector_samples_consumer
  end interface
  interface
    function c_malloc(size) bind(c, name="prik_malloc") result(ptr)
      import :: c_ptr, c_size_t
      integer(c_size_t), value :: size
      type(c_ptr) :: ptr
    end function c_malloc
  end interface
contains
  function bind_c_summarize(&
    & required, &
    & bound_scale, &
    & bound_values, &
    & values_dense_actual, &
    & values_extent_0, &
    & values_upper_bound_0, &
    & values_stride_0, &
    & bound_label, &
    & label_length, &
    & bound_item, &
    & bound_item_access, &
    & bound_item_identity, &
    & bound_item_scoped, &
    & bound_item_checkout, &
    & bound_item_restore, &
    & bound_item_status) result(result) bind(c, name="bind_c_summarize")
    integer(c_int32_t), value :: required
    type(c_ptr), value :: bound_scale
    type(c_ptr), value :: bound_values
    integer(c_int), value :: values_dense_actual
    integer(c_int64_t), value :: values_extent_0
    integer(c_int64_t), value :: values_upper_bound_0
    integer(c_int64_t), value :: values_stride_0
    type(c_ptr), value :: bound_label
    integer(c_int64_t), value :: label_length
    type(c_ptr), value :: bound_item
    integer(c_int), value :: bound_item_access
    type(c_ptr), value :: bound_item_identity
    type(c_funptr), value :: bound_item_scoped
    type(c_funptr), value :: bound_item_checkout
    type(c_funptr), value :: bound_item_restore
    integer(c_int), intent(out) :: bound_item_status
    integer(c_int32_t) :: result
    integer(c_int32_t), pointer :: scale
    real(c_double), pointer, dimension(:) :: values_base
    real(c_double), pointer, dimension(:) :: values
    character(kind=c_char), pointer, dimension(:) :: label_bytes
    character(kind=c_char, len=label_length) :: label
    logical :: prik_derived_ready
    type(prik_type_vector), pointer :: item
    type(prik_vector_allocatable_holder), pointer :: item_allocatable_holder
    type(prik_vector_pointer_holder), pointer :: item_pointer_holder
    type(prik_type_vector), pointer :: item_call_pointer
    type(c_ptr) :: item_transaction_address
    integer(c_int) :: item_holder_status
    integer(c_int) :: item_restore_status
    logical :: item_created
    logical :: item_acquired
    procedure(prik_derived_scoped), pointer :: item_scoped_proc
    procedure(prik_derived_checkout), pointer :: item_checkout_proc
    procedure(prik_derived_restore), pointer :: item_restore_proc
    bound_item_status = 0_c_int
    item_created = .false.
    item_acquired = .false.
    item_transaction_address = c_null_ptr
    nullify(item)
    nullify(item_call_pointer)
    prik_derived_ready = .true.
    select case (bound_item_access)
    case (0)
    case (1)
      if (c_associated(bound_item)) then
        call c_f_pointer(bound_item, item)
      else
        bound_item_status = 1_c_int
      end if
    case (2)
      if (c_associated(bound_item_scoped)) then
        call c_f_procpointer(bound_item_scoped, item_scoped_proc)
      else
        bound_item_status = 6_c_int
      end if
    case (3)
      item_holder_status = 0_c_int
      if (c_associated(bound_item)) then
        call c_f_pointer(bound_item, item_allocatable_holder)
      else
        allocate(item_allocatable_holder, stat=item_holder_status)
        item_created = .true.
      end if
      if (item_holder_status /= 0_c_int) then
        bound_item_status = 4_c_int
      else
        if (allocated(item_allocatable_holder%value)) then
          item => item_allocatable_holder%value
        else
          bound_item_status = 1_c_int
        end if
      end if
    case (4)
      item_holder_status = 0_c_int
      if (c_associated(bound_item)) then
        call c_f_pointer(bound_item, item_pointer_holder)
      else
        allocate(item_pointer_holder, stat=item_holder_status)
        nullify(item_pointer_holder%value)
        item_created = .true.
      end if
      if (item_holder_status /= 0_c_int) then
        bound_item_status = 4_c_int
      else
        if (associated(item_pointer_holder%value)) then
          item => item_pointer_holder%value
        else
          bound_item_status = 1_c_int
        end if
      end if
    case default
      bound_item_status = 6_c_int
    end select
    if (prik_derived_ready) then
      if (bound_item_status == 0_c_int) then
        select case (bound_item_access)
        case (5)
          bound_item_status = item_checkout_proc(item_transaction_address)
          if (bound_item_status == 0_c_int) then
            call c_f_pointer(item_transaction_address, item_allocatable_holder)
            item_acquired = .true.
          end if
        case (6)
          bound_item_status = item_checkout_proc(item_transaction_address)
          if (bound_item_status == 0_c_int) then
            call c_f_pointer(item_transaction_address, item_pointer_holder)
            item_acquired = .true.
          end if
        case default
        end select
        if (bound_item_status /= 0_c_int) then
          prik_derived_ready = .false.
        end if
      else
        prik_derived_ready = .false.
      end if
    end if
    if (prik_derived_ready) then
      call prik_derived_step_0()
    end if
    if (item_acquired) then
      item_restore_status = item_restore_proc(item_transaction_address)
      if (item_restore_status /= 0_c_int) then
        bound_item_status = item_restore_status
      end if
      item_acquired = .false.
    end if
    if (item_created .and. bound_item_access == 3_c_int) then
      deallocate(item_allocatable_holder)
    end if
    if (item_created .and. bound_item_access == 4_c_int) then
      deallocate(item_pointer_holder)
    end if
  contains
    subroutine prik_derived_optional_step_0()
      if (bound_item_access /= 0_c_int) then
        call prik_derived_optional_step_1(item)
      else
        call prik_derived_optional_step_1()
      end if
    end subroutine prik_derived_optional_step_0
    subroutine prik_derived_optional_step_1(prik_optional_item)
      type(prik_type_vector), optional :: prik_optional_item
      if (c_associated(bound_scale)) then
        call c_f_pointer(bound_scale, scale)
        if (c_associated(bound_values)) then
          call c_f_pointer(bound_values, values_base, [values_extent_0])
          if (values_dense_actual /= 0_c_int) then
            values => values_base
          else
            values => values_base(1:values_upper_bound_0 + 1:values_stride_0)
          end if
          if (c_associated(bound_label)) then
            call c_f_pointer(bound_label, label_bytes, [label_length])
            label = transfer(label_bytes, label)
            result = native_summarize(required=required, scale=scale, values=values, label=label, item=prik_optional_item)
          else
            result = native_summarize(required=required, scale=scale, values=values, item=prik_optional_item)
          end if
        else
          if (c_associated(bound_label)) then
            call c_f_pointer(bound_label, label_bytes, [label_length])
            label = transfer(label_bytes, label)
            result = native_summarize(required=required, scale=scale, label=label, item=prik_optional_item)
          else
            result = native_summarize(required=required, scale=scale, item=prik_optional_item)
          end if
        end if
      else
        if (c_associated(bound_values)) then
          call c_f_pointer(bound_values, values_base, [values_extent_0])
          if (values_dense_actual /= 0_c_int) then
            values => values_base
          else
            values => values_base(1:values_upper_bound_0 + 1:values_stride_0)
          end if
          if (c_associated(bound_label)) then
            call c_f_pointer(bound_label, label_bytes, [label_length])
            label = transfer(label_bytes, label)
            result = native_summarize(required=required, values=values, label=label, item=prik_optional_item)
          else
            result = native_summarize(required=required, values=values, item=prik_optional_item)
          end if
        else
          if (c_associated(bound_label)) then
            call c_f_pointer(bound_label, label_bytes, [label_length])
            label = transfer(label_bytes, label)
            result = native_summarize(required=required, label=label, item=prik_optional_item)
          else
            result = native_summarize(required=required, item=prik_optional_item)
          end if
        end if
      end if
    end subroutine prik_derived_optional_step_1
    subroutine prik_derived_step_0()
      if (bound_item_access == 2_c_int) then
        bound_item_status = item_scoped_proc(c_funloc(prik_derived_consumer_0), c_null_ptr)
      else
        call prik_derived_step_1()
      end if
    end subroutine prik_derived_step_0
    function prik_derived_consumer_0(address, context) result(status) bind(c)
      type(c_ptr), value :: address
      type(c_ptr), value :: context
      integer(c_int) :: status
      if (c_associated(address)) then
        call c_f_pointer(address, item)
        call prik_derived_step_1()
        status = 0_c_int
      else
        status = 1_c_int
      end if
    end function prik_derived_consumer_0
    subroutine prik_derived_step_1()
      call prik_derived_optional_step_0()
    end subroutine prik_derived_step_1
  end function bind_c_summarize
  subroutine bind_c_make_values(count, fill_value, result) bind(c, name="bind_c_make_values")
    integer(c_int32_t), value :: count
    real(c_double), value :: fill_value
    real(c_double), allocatable, dimension(:), intent(out) :: result
    real(c_double), allocatable, dimension(:) :: result_value
    result_value = native_make_values(count, fill_value)
    if (allocated(result_value)) then
      call move_alloc(result_value, result)
    else
      if (allocated(result)) then
        deallocate(result)
      end if
    end if
  end subroutine bind_c_make_values
  function bind_c_owned_result_5531b6b6_allocated(&
    & result) result(state) bind(c, name="bind_c_owned_result_5531b6b6_allocated")
    real(c_double), allocatable, dimension(:), intent(in) :: result
    logical(c_bool) :: state
    state = allocated(result)
  end function bind_c_owned_result_5531b6b6_allocated
  subroutine bind_c_owned_result_5531b6b6_deallocate(&
    & result) bind(c, name="bind_c_owned_result_5531b6b6_deallocate")
    real(c_double), allocatable, dimension(:), intent(inout) :: result
    if (allocated(result)) then
      deallocate(result)
    end if
  end subroutine bind_c_owned_result_5531b6b6_deallocate
  subroutine bind_c_owned_result_5531b6b6_destroy(result) bind(c, name="bind_c_owned_result_5531b6b6_destroy")
    real(c_double), allocatable, dimension(:), intent(inout) :: result
    if (allocated(result)) then
      deallocate(result)
    end if
  end subroutine bind_c_owned_result_5531b6b6_destroy
  subroutine bind_c_owned_result_5531b6b6_shape(&
    & result, &
    & extent_0) bind(c, name="bind_c_owned_result_5531b6b6_shape")
    real(c_double), allocatable, dimension(:), intent(in) :: result
    integer(c_int64_t) :: extent_0
    if (allocated(result)) then
      extent_0 = size(result, 1, kind=c_int64_t)
    else
      extent_0 = 0_c_int64_t
    end if
  end subroutine bind_c_owned_result_5531b6b6_shape
  function bind_c_apply_callback(value) result(result) bind(c, name="bind_c_apply_callback")
    real(c_double), value :: value
    real(c_double) :: result
    procedure(prik_scalar_callback_299cdba6) :: prik_callback_adapter_callback_83b3d1d9
    result = native_apply_callback(prik_callback_adapter_callback_83b3d1d9, value)
  end function bind_c_apply_callback
  subroutine bind_c_split_value(value, doubled, status) bind(c, name="bind_c_split_value")
    real(c_double), value :: value
    real(c_double) :: doubled
    integer(c_int32_t) :: status
    call native_split_value(value, doubled, status)
  end subroutine bind_c_split_value
  subroutine bind_c_reset_allocatable_item(&
    & bound_value, &
    & bound_value_access, &
    & bound_value_identity, &
    & bound_value_scoped, &
    & bound_value_checkout, &
    & bound_value_restore, &
    & bound_value_status, &
    & bound_value_output, &
    & bound_value_output_present) bind(c, name="bind_c_reset_allocatable_item")
    type(c_ptr), value :: bound_value
    integer(c_int), value :: bound_value_access
    type(c_ptr), value :: bound_value_identity
    type(c_funptr), value :: bound_value_scoped
    type(c_funptr), value :: bound_value_checkout
    type(c_funptr), value :: bound_value_restore
    integer(c_int), intent(out) :: bound_value_status
    type(c_ptr), intent(out) :: bound_value_output
    integer(c_int), intent(out) :: bound_value_output_present
    logical :: prik_derived_ready
    type(prik_type_holder_item), pointer :: value
    type(prik_holder_item_allocatable_holder), pointer :: value_allocatable_holder
    type(prik_holder_item_pointer_holder), pointer :: value_pointer_holder
    type(prik_type_holder_item), pointer :: value_call_pointer
    type(c_ptr) :: value_transaction_address
    integer(c_int) :: value_holder_status
    integer(c_int) :: value_restore_status
    logical :: value_created
    logical :: value_acquired
    procedure(prik_derived_scoped), pointer :: value_scoped_proc
    procedure(prik_derived_checkout), pointer :: value_checkout_proc
    procedure(prik_derived_restore), pointer :: value_restore_proc
    bound_value_status = 0_c_int
    value_created = .false.
    value_acquired = .false.
    value_transaction_address = c_null_ptr
    nullify(value)
    nullify(value_call_pointer)
    bound_value_output = c_null_ptr
    bound_value_output_present = 0_c_int
    prik_derived_ready = .true.
    select case (bound_value_access)
    case (0)
    case (3)
      value_holder_status = 0_c_int
      if (c_associated(bound_value)) then
        call c_f_pointer(bound_value, value_allocatable_holder)
      else
        allocate(value_allocatable_holder, stat=value_holder_status)
        value_created = .true.
      end if
      if (value_holder_status /= 0_c_int) then
        bound_value_status = 4_c_int
      end if
    case (5)
      if (c_associated(bound_value_checkout) .and. c_associated(bound_value_restore)) then
        call c_f_procpointer(bound_value_checkout, value_checkout_proc)
        call c_f_procpointer(bound_value_restore, value_restore_proc)
      else
        bound_value_status = 6_c_int
      end if
    case default
      bound_value_status = 6_c_int
    end select
    if (prik_derived_ready) then
      if (bound_value_status == 0_c_int) then
        select case (bound_value_access)
        case (5)
          bound_value_status = value_checkout_proc(value_transaction_address)
          if (bound_value_status == 0_c_int) then
            call c_f_pointer(value_transaction_address, value_allocatable_holder)
            value_acquired = .true.
          end if
        case (6)
          bound_value_status = value_checkout_proc(value_transaction_address)
          if (bound_value_status == 0_c_int) then
            call c_f_pointer(value_transaction_address, value_pointer_holder)
            value_acquired = .true.
          end if
        case default
        end select
        if (bound_value_status /= 0_c_int) then
          prik_derived_ready = .false.
        end if
      else
        prik_derived_ready = .false.
      end if
    end if
    if (prik_derived_ready) then
      call native_reset_allocatable_item(value_allocatable_holder%value)
    end if
    if (value_acquired) then
      value_restore_status = value_restore_proc(value_transaction_address)
      if (value_restore_status /= 0_c_int) then
        bound_value_status = value_restore_status
      end if
      value_acquired = .false.
    end if
    if (bound_value_access == 3_c_int) then
      bound_value_output = c_loc(value_allocatable_holder)
      if (allocated(value_allocatable_holder%value)) then
        bound_value_output_present = 1_c_int
      else
        bound_value_output_present = 0_c_int
      end if
    else
      if (bound_value_access == 4_c_int) then
        bound_value_output = c_loc(value_pointer_holder)
        if (associated(value_pointer_holder%value)) then
          bound_value_output_present = 1_c_int
        else
          bound_value_output_present = 0_c_int
        end if
      else
        if (bound_value_access == 5_c_int .or. bound_value_access == 6_c_int) then
          bound_value_output_present = 1_c_int
        end if
      end if
    end if
  end subroutine bind_c_reset_allocatable_item
  subroutine bind_c_shift_pointer_item(&
    & bound_value, &
    & bound_value_access, &
    & bound_value_identity, &
    & bound_value_scoped, &
    & bound_value_checkout, &
    & bound_value_restore, &
    & bound_value_status, &
    & bound_value_output, &
    & bound_value_output_present, &
    & amount) bind(c, name="bind_c_shift_pointer_item")
    type(c_ptr), value :: bound_value
    integer(c_int), value :: bound_value_access
    type(c_ptr), value :: bound_value_identity
    type(c_funptr), value :: bound_value_scoped
    type(c_funptr), value :: bound_value_checkout
    type(c_funptr), value :: bound_value_restore
    integer(c_int), intent(out) :: bound_value_status
    type(c_ptr), intent(out) :: bound_value_output
    integer(c_int), intent(out) :: bound_value_output_present
    real(c_double), value :: amount
    logical :: prik_derived_ready
    type(prik_type_holder_item), pointer :: value
    type(prik_holder_item_allocatable_holder), pointer :: value_allocatable_holder
    type(prik_holder_item_pointer_holder), pointer :: value_pointer_holder
    type(prik_type_holder_item), pointer :: value_call_pointer
    type(c_ptr) :: value_transaction_address
    integer(c_int) :: value_holder_status
    integer(c_int) :: value_restore_status
    logical :: value_created
    logical :: value_acquired
    procedure(prik_derived_scoped), pointer :: value_scoped_proc
    procedure(prik_derived_checkout), pointer :: value_checkout_proc
    procedure(prik_derived_restore), pointer :: value_restore_proc
    bound_value_status = 0_c_int
    value_created = .false.
    value_acquired = .false.
    value_transaction_address = c_null_ptr
    nullify(value)
    nullify(value_call_pointer)
    bound_value_output = c_null_ptr
    bound_value_output_present = 0_c_int
    prik_derived_ready = .true.
    select case (bound_value_access)
    case (0)
    case (4)
      value_holder_status = 0_c_int
      if (c_associated(bound_value)) then
        call c_f_pointer(bound_value, value_pointer_holder)
      else
        allocate(value_pointer_holder, stat=value_holder_status)
        nullify(value_pointer_holder%value)
        value_created = .true.
      end if
      if (value_holder_status /= 0_c_int) then
        bound_value_status = 4_c_int
      end if
    case (6)
      if (c_associated(bound_value_checkout) .and. c_associated(bound_value_restore)) then
        call c_f_procpointer(bound_value_checkout, value_checkout_proc)
        call c_f_procpointer(bound_value_restore, value_restore_proc)
      else
        bound_value_status = 6_c_int
      end if
    case default
      bound_value_status = 6_c_int
    end select
    if (prik_derived_ready) then
      if (bound_value_status == 0_c_int) then
        select case (bound_value_access)
        case (5)
          bound_value_status = value_checkout_proc(value_transaction_address)
          if (bound_value_status == 0_c_int) then
            call c_f_pointer(value_transaction_address, value_allocatable_holder)
            value_acquired = .true.
          end if
        case (6)
          bound_value_status = value_checkout_proc(value_transaction_address)
          if (bound_value_status == 0_c_int) then
            call c_f_pointer(value_transaction_address, value_pointer_holder)
            value_acquired = .true.
          end if
        case default
        end select
        if (bound_value_status /= 0_c_int) then
          prik_derived_ready = .false.
        end if
      else
        prik_derived_ready = .false.
      end if
    end if
    if (prik_derived_ready) then
      if (bound_value_access == 4_c_int .or. bound_value_access == 6_c_int) then
        if (associated(value_pointer_holder%value)) then
          value_call_pointer => value_pointer_holder%value
        else
          nullify(value_call_pointer)
        end if
      else
        if (associated(value)) then
          value_call_pointer => value
        else
          nullify(value_call_pointer)
        end if
      end if
      call native_shift_pointer_item(value_call_pointer, amount)
      if (bound_value_access == 4_c_int .or. bound_value_access == 6_c_int) then
        if (associated(value_call_pointer)) then
          value_pointer_holder%value => value_call_pointer
        else
          nullify(value_pointer_holder%value)
        end if
      end if
    end if
    if (value_acquired) then
      value_restore_status = value_restore_proc(value_transaction_address)
      if (value_restore_status /= 0_c_int) then
        bound_value_status = value_restore_status
      end if
      value_acquired = .false.
    end if
    if (bound_value_access == 3_c_int) then
      bound_value_output = c_loc(value_allocatable_holder)
      if (allocated(value_allocatable_holder%value)) then
        bound_value_output_present = 1_c_int
      else
        bound_value_output_present = 0_c_int
      end if
    else
      if (bound_value_access == 4_c_int) then
        bound_value_output = c_loc(value_pointer_holder)
        if (associated(value_pointer_holder%value)) then
          bound_value_output_present = 1_c_int
        else
          bound_value_output_present = 0_c_int
        end if
      else
        if (bound_value_access == 5_c_int .or. bound_value_access == 6_c_int) then
          bound_value_output_present = 1_c_int
        end if
      end if
    end if
  end subroutine bind_c_shift_pointer_item
  subroutine bind_c__prik_class_vector_scale(&
    & bound_self, &
    & bound_self_access, &
    & bound_self_identity, &
    & bound_self_polymorphic, &
    & bound_self_scoped, &
    & bound_self_checkout, &
    & bound_self_restore, &
    & bound_self_status, &
    & factor) bind(c, name="bind_c__prik_class_vector_scale")
    type(c_ptr), value :: bound_self
    integer(c_int), value :: bound_self_access
    type(c_ptr), value :: bound_self_identity
    integer(c_int), value :: bound_self_polymorphic
    type(c_funptr), value :: bound_self_scoped
    type(c_funptr), value :: bound_self_checkout
    type(c_funptr), value :: bound_self_restore
    integer(c_int), intent(out) :: bound_self_status
    real(c_double), value :: factor
    logical :: prik_derived_ready
    type(prik_type_vector), pointer :: self
    type(prik_vector_allocatable_holder), pointer :: self_allocatable_holder
    type(prik_vector_pointer_holder), pointer :: self_pointer_holder
    type(prik_type_vector), pointer :: self_call_pointer
    type(c_ptr) :: self_transaction_address
    integer(c_int) :: self_holder_status
    integer(c_int) :: self_restore_status
    logical :: self_created
    logical :: self_acquired
    procedure(prik_derived_scoped), pointer :: self_scoped_proc
    procedure(prik_derived_checkout), pointer :: self_checkout_proc
    procedure(prik_derived_restore), pointer :: self_restore_proc
    type(prik_type_vector), pointer :: self_polymorphic_1
    bound_self_status = 0_c_int
    self_created = .false.
    self_acquired = .false.
    self_transaction_address = c_null_ptr
    nullify(self)
    nullify(self_call_pointer)
    prik_derived_ready = .true.
    select case (bound_self_access)
    case (0)
    case (1)
      select case (bound_self_polymorphic)
      case (1)
        if (c_associated(bound_self)) then
          call c_f_pointer(bound_self, self_polymorphic_1)
        else
          bound_self_status = 1_c_int
        end if
      case default
        bound_self_status = 6_c_int
      end select
    case (2)
      if (c_associated(bound_self_scoped)) then
        call c_f_procpointer(bound_self_scoped, self_scoped_proc)
      else
        bound_self_status = 6_c_int
      end if
    case (3)
      self_holder_status = 0_c_int
      if (c_associated(bound_self)) then
        call c_f_pointer(bound_self, self_allocatable_holder)
      else
        allocate(self_allocatable_holder, stat=self_holder_status)
        self_created = .true.
      end if
      if (self_holder_status /= 0_c_int) then
        bound_self_status = 4_c_int
      else
        if (allocated(self_allocatable_holder%value)) then
          self => self_allocatable_holder%value
        else
          bound_self_status = 1_c_int
        end if
      end if
    case (4)
      self_holder_status = 0_c_int
      if (c_associated(bound_self)) then
        call c_f_pointer(bound_self, self_pointer_holder)
      else
        allocate(self_pointer_holder, stat=self_holder_status)
        nullify(self_pointer_holder%value)
        self_created = .true.
      end if
      if (self_holder_status /= 0_c_int) then
        bound_self_status = 4_c_int
      else
        if (associated(self_pointer_holder%value)) then
          self => self_pointer_holder%value
        else
          bound_self_status = 1_c_int
        end if
      end if
    case default
      bound_self_status = 6_c_int
    end select
    if (prik_derived_ready) then
      if (bound_self_status == 0_c_int) then
        select case (bound_self_access)
        case (5)
          bound_self_status = self_checkout_proc(self_transaction_address)
          if (bound_self_status == 0_c_int) then
            call c_f_pointer(self_transaction_address, self_allocatable_holder)
            self_acquired = .true.
          end if
        case (6)
          bound_self_status = self_checkout_proc(self_transaction_address)
          if (bound_self_status == 0_c_int) then
            call c_f_pointer(self_transaction_address, self_pointer_holder)
            self_acquired = .true.
          end if
        case default
        end select
        if (bound_self_status /= 0_c_int) then
          prik_derived_ready = .false.
        end if
      else
        prik_derived_ready = .false.
      end if
    end if
    if (prik_derived_ready) then
      call prik_derived_step_0()
    end if
    if (self_acquired) then
      self_restore_status = self_restore_proc(self_transaction_address)
      if (self_restore_status /= 0_c_int) then
        bound_self_status = self_restore_status
      end if
      self_acquired = .false.
    end if
    if (self_created .and. bound_self_access == 3_c_int) then
      deallocate(self_allocatable_holder)
    end if
    if (self_created .and. bound_self_access == 4_c_int) then
      deallocate(self_pointer_holder)
    end if
  contains
    subroutine prik_derived_step_0()
      if (bound_self_access == 2_c_int) then
        bound_self_status = self_scoped_proc(c_funloc(prik_derived_consumer_0), c_null_ptr)
      else
        call prik_derived_step_1()
      end if
    end subroutine prik_derived_step_0
    function prik_derived_consumer_0(address, context) result(status) bind(c)
      type(c_ptr), value :: address
      type(c_ptr), value :: context
      integer(c_int) :: status
      if (c_associated(address)) then
        call c_f_pointer(address, self)
        call prik_derived_step_1()
        status = 0_c_int
      else
        status = 1_c_int
      end if
    end function prik_derived_consumer_0
    subroutine prik_derived_step_1()
      select case (bound_self_polymorphic)
      case (1)
        call self_polymorphic_1%scale(factor)
      case default
      end select
    end subroutine prik_derived_step_1
  end subroutine bind_c__prik_class_vector_scale
  subroutine bind_c__prik_class_vector_shift(&
    & dx, &
    & bound_owner, &
    & bound_owner_access, &
    & bound_owner_identity, &
    & bound_owner_polymorphic, &
    & bound_owner_scoped, &
    & bound_owner_checkout, &
    & bound_owner_restore, &
    & bound_owner_status, &
    & dy) bind(c, name="bind_c__prik_class_vector_shift")
    real(c_double), value :: dx
    type(c_ptr), value :: bound_owner
    integer(c_int), value :: bound_owner_access
    type(c_ptr), value :: bound_owner_identity
    integer(c_int), value :: bound_owner_polymorphic
    type(c_funptr), value :: bound_owner_scoped
    type(c_funptr), value :: bound_owner_checkout
    type(c_funptr), value :: bound_owner_restore
    integer(c_int), intent(out) :: bound_owner_status
    real(c_double), value :: dy
    logical :: prik_derived_ready
    type(prik_type_vector), pointer :: owner
    type(prik_vector_allocatable_holder), pointer :: owner_allocatable_holder
    type(prik_vector_pointer_holder), pointer :: owner_pointer_holder
    type(prik_type_vector), pointer :: owner_call_pointer
    type(c_ptr) :: owner_transaction_address
    integer(c_int) :: owner_holder_status
    integer(c_int) :: owner_restore_status
    logical :: owner_created
    logical :: owner_acquired
    procedure(prik_derived_scoped), pointer :: owner_scoped_proc
    procedure(prik_derived_checkout), pointer :: owner_checkout_proc
    procedure(prik_derived_restore), pointer :: owner_restore_proc
    type(prik_type_vector), pointer :: owner_polymorphic_1
    bound_owner_status = 0_c_int
    owner_created = .false.
    owner_acquired = .false.
    owner_transaction_address = c_null_ptr
    nullify(owner)
    nullify(owner_call_pointer)
    prik_derived_ready = .true.
    select case (bound_owner_access)
    case (0)
    case (1)
      select case (bound_owner_polymorphic)
      case (1)
        if (c_associated(bound_owner)) then
          call c_f_pointer(bound_owner, owner_polymorphic_1)
        else
          bound_owner_status = 1_c_int
        end if
      case default
        bound_owner_status = 6_c_int
      end select
    case (2)
      if (c_associated(bound_owner_scoped)) then
        call c_f_procpointer(bound_owner_scoped, owner_scoped_proc)
      else
        bound_owner_status = 6_c_int
      end if
    case (3)
      owner_holder_status = 0_c_int
      if (c_associated(bound_owner)) then
        call c_f_pointer(bound_owner, owner_allocatable_holder)
      else
        allocate(owner_allocatable_holder, stat=owner_holder_status)
        owner_created = .true.
      end if
      if (owner_holder_status /= 0_c_int) then
        bound_owner_status = 4_c_int
      else
        if (allocated(owner_allocatable_holder%value)) then
          owner => owner_allocatable_holder%value
        else
          bound_owner_status = 1_c_int
        end if
      end if
    case (4)
      owner_holder_status = 0_c_int
      if (c_associated(bound_owner)) then
        call c_f_pointer(bound_owner, owner_pointer_holder)
      else
        allocate(owner_pointer_holder, stat=owner_holder_status)
        nullify(owner_pointer_holder%value)
        owner_created = .true.
      end if
      if (owner_holder_status /= 0_c_int) then
        bound_owner_status = 4_c_int
      else
        if (associated(owner_pointer_holder%value)) then
          owner => owner_pointer_holder%value
        else
          bound_owner_status = 1_c_int
        end if
      end if
    case default
      bound_owner_status = 6_c_int
    end select
    if (prik_derived_ready) then
      if (bound_owner_status == 0_c_int) then
        select case (bound_owner_access)
        case (5)
          bound_owner_status = owner_checkout_proc(owner_transaction_address)
          if (bound_owner_status == 0_c_int) then
            call c_f_pointer(owner_transaction_address, owner_allocatable_holder)
            owner_acquired = .true.
          end if
        case (6)
          bound_owner_status = owner_checkout_proc(owner_transaction_address)
          if (bound_owner_status == 0_c_int) then
            call c_f_pointer(owner_transaction_address, owner_pointer_holder)
            owner_acquired = .true.
          end if
        case default
        end select
        if (bound_owner_status /= 0_c_int) then
          prik_derived_ready = .false.
        end if
      else
        prik_derived_ready = .false.
      end if
    end if
    if (prik_derived_ready) then
      call prik_derived_step_0()
    end if
    if (owner_acquired) then
      owner_restore_status = owner_restore_proc(owner_transaction_address)
      if (owner_restore_status /= 0_c_int) then
        bound_owner_status = owner_restore_status
      end if
      owner_acquired = .false.
    end if
    if (owner_created .and. bound_owner_access == 3_c_int) then
      deallocate(owner_allocatable_holder)
    end if
    if (owner_created .and. bound_owner_access == 4_c_int) then
      deallocate(owner_pointer_holder)
    end if
  contains
    subroutine prik_derived_step_0()
      if (bound_owner_access == 2_c_int) then
        bound_owner_status = owner_scoped_proc(c_funloc(prik_derived_consumer_0), c_null_ptr)
      else
        call prik_derived_step_1()
      end if
    end subroutine prik_derived_step_0
    function prik_derived_consumer_0(address, context) result(status) bind(c)
      type(c_ptr), value :: address
      type(c_ptr), value :: context
      integer(c_int) :: status
      if (c_associated(address)) then
        call c_f_pointer(address, owner)
        call prik_derived_step_1()
        status = 0_c_int
      else
        status = 1_c_int
      end if
    end function prik_derived_consumer_0
    subroutine prik_derived_step_1()
      select case (bound_owner_polymorphic)
      case (1)
        call owner_polymorphic_1%shift(dx, dy)
      case default
      end select
    end subroutine prik_derived_step_1
  end subroutine bind_c__prik_class_vector_shift
  function bind_c__prik_class_vector_magnitude(&
    & bound_self, &
    & bound_self_access, &
    & bound_self_identity, &
    & bound_self_polymorphic, &
    & bound_self_scoped, &
    & bound_self_checkout, &
    & bound_self_restore, &
    & bound_self_status) result(result) bind(c, name="bind_c__prik_class_vector_magnitude")
    type(c_ptr), value :: bound_self
    integer(c_int), value :: bound_self_access
    type(c_ptr), value :: bound_self_identity
    integer(c_int), value :: bound_self_polymorphic
    type(c_funptr), value :: bound_self_scoped
    type(c_funptr), value :: bound_self_checkout
    type(c_funptr), value :: bound_self_restore
    integer(c_int), intent(out) :: bound_self_status
    real(c_double) :: result
    logical :: prik_derived_ready
    type(prik_type_vector), pointer :: self
    type(prik_vector_allocatable_holder), pointer :: self_allocatable_holder
    type(prik_vector_pointer_holder), pointer :: self_pointer_holder
    type(prik_type_vector), pointer :: self_call_pointer
    type(c_ptr) :: self_transaction_address
    integer(c_int) :: self_holder_status
    integer(c_int) :: self_restore_status
    logical :: self_created
    logical :: self_acquired
    procedure(prik_derived_scoped), pointer :: self_scoped_proc
    procedure(prik_derived_checkout), pointer :: self_checkout_proc
    procedure(prik_derived_restore), pointer :: self_restore_proc
    type(prik_type_vector), pointer :: self_polymorphic_1
    bound_self_status = 0_c_int
    self_created = .false.
    self_acquired = .false.
    self_transaction_address = c_null_ptr
    nullify(self)
    nullify(self_call_pointer)
    prik_derived_ready = .true.
    select case (bound_self_access)
    case (0)
    case (1)
      select case (bound_self_polymorphic)
      case (1)
        if (c_associated(bound_self)) then
          call c_f_pointer(bound_self, self_polymorphic_1)
        else
          bound_self_status = 1_c_int
        end if
      case default
        bound_self_status = 6_c_int
      end select
    case (2)
      if (c_associated(bound_self_scoped)) then
        call c_f_procpointer(bound_self_scoped, self_scoped_proc)
      else
        bound_self_status = 6_c_int
      end if
    case (3)
      self_holder_status = 0_c_int
      if (c_associated(bound_self)) then
        call c_f_pointer(bound_self, self_allocatable_holder)
      else
        allocate(self_allocatable_holder, stat=self_holder_status)
        self_created = .true.
      end if
      if (self_holder_status /= 0_c_int) then
        bound_self_status = 4_c_int
      else
        if (allocated(self_allocatable_holder%value)) then
          self => self_allocatable_holder%value
        else
          bound_self_status = 1_c_int
        end if
      end if
    case (4)
      self_holder_status = 0_c_int
      if (c_associated(bound_self)) then
        call c_f_pointer(bound_self, self_pointer_holder)
      else
        allocate(self_pointer_holder, stat=self_holder_status)
        nullify(self_pointer_holder%value)
        self_created = .true.
      end if
      if (self_holder_status /= 0_c_int) then
        bound_self_status = 4_c_int
      else
        if (associated(self_pointer_holder%value)) then
          self => self_pointer_holder%value
        else
          bound_self_status = 1_c_int
        end if
      end if
    case default
      bound_self_status = 6_c_int
    end select
    if (prik_derived_ready) then
      if (bound_self_status == 0_c_int) then
        select case (bound_self_access)
        case (5)
          bound_self_status = self_checkout_proc(self_transaction_address)
          if (bound_self_status == 0_c_int) then
            call c_f_pointer(self_transaction_address, self_allocatable_holder)
            self_acquired = .true.
          end if
        case (6)
          bound_self_status = self_checkout_proc(self_transaction_address)
          if (bound_self_status == 0_c_int) then
            call c_f_pointer(self_transaction_address, self_pointer_holder)
            self_acquired = .true.
          end if
        case default
        end select
        if (bound_self_status /= 0_c_int) then
          prik_derived_ready = .false.
        end if
      else
        prik_derived_ready = .false.
      end if
    end if
    if (prik_derived_ready) then
      call prik_derived_step_0()
    end if
    if (self_acquired) then
      self_restore_status = self_restore_proc(self_transaction_address)
      if (self_restore_status /= 0_c_int) then
        bound_self_status = self_restore_status
      end if
      self_acquired = .false.
    end if
    if (self_created .and. bound_self_access == 3_c_int) then
      deallocate(self_allocatable_holder)
    end if
    if (self_created .and. bound_self_access == 4_c_int) then
      deallocate(self_pointer_holder)
    end if
  contains
    subroutine prik_derived_step_0()
      if (bound_self_access == 2_c_int) then
        bound_self_status = self_scoped_proc(c_funloc(prik_derived_consumer_0), c_null_ptr)
      else
        call prik_derived_step_1()
      end if
    end subroutine prik_derived_step_0
    function prik_derived_consumer_0(address, context) result(status) bind(c)
      type(c_ptr), value :: address
      type(c_ptr), value :: context
      integer(c_int) :: status
      if (c_associated(address)) then
        call c_f_pointer(address, self)
        call prik_derived_step_1()
        status = 0_c_int
      else
        status = 1_c_int
      end if
    end function prik_derived_consumer_0
    subroutine prik_derived_step_1()
      select case (bound_self_polymorphic)
      case (1)
        result = self_polymorphic_1%magnitude()
      case default
      end select
    end subroutine prik_derived_step_1
  end function bind_c__prik_class_vector_magnitude
  subroutine bind_c__prik_class_vector_replace_samples(&
    & bound_self, &
    & bound_self_access, &
    & bound_self_identity, &
    & bound_self_polymorphic, &
    & bound_self_scoped, &
    & bound_self_checkout, &
    & bound_self_restore, &
    & bound_self_status, &
    & bound_values, &
    & values_dense_actual, &
    & values_extent_0, &
    & values_upper_bound_0, &
    & values_stride_0) bind(c, name="bind_c__prik_class_vector_replace_samples")
    type(c_ptr), value :: bound_self
    integer(c_int), value :: bound_self_access
    type(c_ptr), value :: bound_self_identity
    integer(c_int), value :: bound_self_polymorphic
    type(c_funptr), value :: bound_self_scoped
    type(c_funptr), value :: bound_self_checkout
    type(c_funptr), value :: bound_self_restore
    integer(c_int), intent(out) :: bound_self_status
    type(c_ptr), value :: bound_values
    integer(c_int), value :: values_dense_actual
    integer(c_int64_t), value :: values_extent_0
    integer(c_int64_t), value :: values_upper_bound_0
    integer(c_int64_t), value :: values_stride_0
    real(c_double), pointer, dimension(:) :: values_base
    real(c_double), pointer, dimension(:) :: values
    logical :: prik_derived_ready
    type(prik_type_vector), pointer :: self
    type(prik_vector_allocatable_holder), pointer :: self_allocatable_holder
    type(prik_vector_pointer_holder), pointer :: self_pointer_holder
    type(prik_type_vector), pointer :: self_call_pointer
    type(c_ptr) :: self_transaction_address
    integer(c_int) :: self_holder_status
    integer(c_int) :: self_restore_status
    logical :: self_created
    logical :: self_acquired
    procedure(prik_derived_scoped), pointer :: self_scoped_proc
    procedure(prik_derived_checkout), pointer :: self_checkout_proc
    procedure(prik_derived_restore), pointer :: self_restore_proc
    type(prik_type_vector), pointer :: self_polymorphic_1
    call c_f_pointer(bound_values, values_base, [values_extent_0])
    if (values_dense_actual /= 0_c_int) then
      values => values_base
    else
      values => values_base(1:values_upper_bound_0 + 1:values_stride_0)
    end if
    bound_self_status = 0_c_int
    self_created = .false.
    self_acquired = .false.
    self_transaction_address = c_null_ptr
    nullify(self)
    nullify(self_call_pointer)
    prik_derived_ready = .true.
    select case (bound_self_access)
    case (0)
    case (1)
      select case (bound_self_polymorphic)
      case (1)
        if (c_associated(bound_self)) then
          call c_f_pointer(bound_self, self_polymorphic_1)
        else
          bound_self_status = 1_c_int
        end if
      case default
        bound_self_status = 6_c_int
      end select
    case (2)
      if (c_associated(bound_self_scoped)) then
        call c_f_procpointer(bound_self_scoped, self_scoped_proc)
      else
        bound_self_status = 6_c_int
      end if
    case (3)
      self_holder_status = 0_c_int
      if (c_associated(bound_self)) then
        call c_f_pointer(bound_self, self_allocatable_holder)
      else
        allocate(self_allocatable_holder, stat=self_holder_status)
        self_created = .true.
      end if
      if (self_holder_status /= 0_c_int) then
        bound_self_status = 4_c_int
      else
        if (allocated(self_allocatable_holder%value)) then
          self => self_allocatable_holder%value
        else
          bound_self_status = 1_c_int
        end if
      end if
    case (4)
      self_holder_status = 0_c_int
      if (c_associated(bound_self)) then
        call c_f_pointer(bound_self, self_pointer_holder)
      else
        allocate(self_pointer_holder, stat=self_holder_status)
        nullify(self_pointer_holder%value)
        self_created = .true.
      end if
      if (self_holder_status /= 0_c_int) then
        bound_self_status = 4_c_int
      else
        if (associated(self_pointer_holder%value)) then
          self => self_pointer_holder%value
        else
          bound_self_status = 1_c_int
        end if
      end if
    case default
      bound_self_status = 6_c_int
    end select
    if (prik_derived_ready) then
      if (bound_self_status == 0_c_int) then
        select case (bound_self_access)
        case (5)
          bound_self_status = self_checkout_proc(self_transaction_address)
          if (bound_self_status == 0_c_int) then
            call c_f_pointer(self_transaction_address, self_allocatable_holder)
            self_acquired = .true.
          end if
        case (6)
          bound_self_status = self_checkout_proc(self_transaction_address)
          if (bound_self_status == 0_c_int) then
            call c_f_pointer(self_transaction_address, self_pointer_holder)
            self_acquired = .true.
          end if
        case default
        end select
        if (bound_self_status /= 0_c_int) then
          prik_derived_ready = .false.
        end if
      else
        prik_derived_ready = .false.
      end if
    end if
    if (prik_derived_ready) then
      call prik_derived_step_0()
    end if
    if (self_acquired) then
      self_restore_status = self_restore_proc(self_transaction_address)
      if (self_restore_status /= 0_c_int) then
        bound_self_status = self_restore_status
      end if
      self_acquired = .false.
    end if
    if (self_created .and. bound_self_access == 3_c_int) then
      deallocate(self_allocatable_holder)
    end if
    if (self_created .and. bound_self_access == 4_c_int) then
      deallocate(self_pointer_holder)
    end if
  contains
    subroutine prik_derived_step_0()
      if (bound_self_access == 2_c_int) then
        bound_self_status = self_scoped_proc(c_funloc(prik_derived_consumer_0), c_null_ptr)
      else
        call prik_derived_step_1()
      end if
    end subroutine prik_derived_step_0
    function prik_derived_consumer_0(address, context) result(status) bind(c)
      type(c_ptr), value :: address
      type(c_ptr), value :: context
      integer(c_int) :: status
      if (c_associated(address)) then
        call c_f_pointer(address, self)
        call prik_derived_step_1()
        status = 0_c_int
      else
        status = 1_c_int
      end if
    end function prik_derived_consumer_0
    subroutine prik_derived_step_1()
      select case (bound_self_polymorphic)
      case (1)
        call self_polymorphic_1%replace_samples(values)
      case default
      end select
    end subroutine prik_derived_step_1
  end subroutine bind_c__prik_class_vector_replace_samples
  function bind_c__prik_class_vector___add___0(&
    & bound_left, &
    & bound_left_access, &
    & bound_left_identity, &
    & bound_left_polymorphic, &
    & bound_left_scoped, &
    & bound_left_checkout, &
    & bound_left_restore, &
    & bound_left_status, &
    & bound_right, &
    & bound_right_access, &
    & bound_right_identity, &
    & bound_right_scoped, &
    & bound_right_checkout, &
    & bound_right_restore, &
    & bound_right_status) result(result) bind(c, name="bind_c__prik_class_vector___add___0")
    type(c_ptr), value :: bound_left
    integer(c_int), value :: bound_left_access
    type(c_ptr), value :: bound_left_identity
    integer(c_int), value :: bound_left_polymorphic
    type(c_funptr), value :: bound_left_scoped
    type(c_funptr), value :: bound_left_checkout
    type(c_funptr), value :: bound_left_restore
    integer(c_int), intent(out) :: bound_left_status
    type(c_ptr), value :: bound_right
    integer(c_int), value :: bound_right_access
    type(c_ptr), value :: bound_right_identity
    type(c_funptr), value :: bound_right_scoped
    type(c_funptr), value :: bound_right_checkout
    type(c_funptr), value :: bound_right_restore
    integer(c_int), intent(out) :: bound_right_status
    type(c_ptr) :: result
    logical :: prik_derived_ready
    type(prik_type_vector), pointer :: left
    type(prik_vector_allocatable_holder), pointer :: left_allocatable_holder
    type(prik_vector_pointer_holder), pointer :: left_pointer_holder
    type(prik_type_vector), pointer :: left_call_pointer
    type(c_ptr) :: left_transaction_address
    integer(c_int) :: left_holder_status
    integer(c_int) :: left_restore_status
    logical :: left_created
    logical :: left_acquired
    procedure(prik_derived_scoped), pointer :: left_scoped_proc
    procedure(prik_derived_checkout), pointer :: left_checkout_proc
    procedure(prik_derived_restore), pointer :: left_restore_proc
    type(prik_type_vector), pointer :: left_polymorphic_1
    type(prik_type_vector), pointer :: right
    type(prik_vector_allocatable_holder), pointer :: right_allocatable_holder
    type(prik_vector_pointer_holder), pointer :: right_pointer_holder
    type(prik_type_vector), pointer :: right_call_pointer
    type(c_ptr) :: right_transaction_address
    integer(c_int) :: right_holder_status
    integer(c_int) :: right_restore_status
    logical :: right_created
    logical :: right_acquired
    procedure(prik_derived_scoped), pointer :: right_scoped_proc
    procedure(prik_derived_checkout), pointer :: right_checkout_proc
    procedure(prik_derived_restore), pointer :: right_restore_proc
    type(prik_type_vector), pointer :: result_value
    integer(c_int) :: prik_allocation_status
    bound_left_status = 0_c_int
    left_created = .false.
    left_acquired = .false.
    left_transaction_address = c_null_ptr
    nullify(left)
    nullify(left_call_pointer)
    bound_right_status = 0_c_int
    right_created = .false.
    right_acquired = .false.
    right_transaction_address = c_null_ptr
    nullify(right)
    nullify(right_call_pointer)
    prik_derived_ready = .true.
    select case (bound_left_access)
    case (0)
    case (1)
      select case (bound_left_polymorphic)
      case (1)
        if (c_associated(bound_left)) then
          call c_f_pointer(bound_left, left_polymorphic_1)
        else
          bound_left_status = 1_c_int
        end if
      case default
        bound_left_status = 6_c_int
      end select
    case (2)
      if (c_associated(bound_left_scoped)) then
        call c_f_procpointer(bound_left_scoped, left_scoped_proc)
      else
        bound_left_status = 6_c_int
      end if
    case (3)
      left_holder_status = 0_c_int
      if (c_associated(bound_left)) then
        call c_f_pointer(bound_left, left_allocatable_holder)
      else
        allocate(left_allocatable_holder, stat=left_holder_status)
        left_created = .true.
      end if
      if (left_holder_status /= 0_c_int) then
        bound_left_status = 4_c_int
      else
        if (allocated(left_allocatable_holder%value)) then
          left => left_allocatable_holder%value
        else
          bound_left_status = 1_c_int
        end if
      end if
    case (4)
      left_holder_status = 0_c_int
      if (c_associated(bound_left)) then
        call c_f_pointer(bound_left, left_pointer_holder)
      else
        allocate(left_pointer_holder, stat=left_holder_status)
        nullify(left_pointer_holder%value)
        left_created = .true.
      end if
      if (left_holder_status /= 0_c_int) then
        bound_left_status = 4_c_int
      else
        if (associated(left_pointer_holder%value)) then
          left => left_pointer_holder%value
        else
          bound_left_status = 1_c_int
        end if
      end if
    case default
      bound_left_status = 6_c_int
    end select
    select case (bound_right_access)
    case (0)
    case (1)
      if (c_associated(bound_right)) then
        call c_f_pointer(bound_right, right)
      else
        bound_right_status = 1_c_int
      end if
    case (2)
      if (c_associated(bound_right_scoped)) then
        call c_f_procpointer(bound_right_scoped, right_scoped_proc)
      else
        bound_right_status = 6_c_int
      end if
    case (3)
      right_holder_status = 0_c_int
      if (c_associated(bound_right)) then
        call c_f_pointer(bound_right, right_allocatable_holder)
      else
        allocate(right_allocatable_holder, stat=right_holder_status)
        right_created = .true.
      end if
      if (right_holder_status /= 0_c_int) then
        bound_right_status = 4_c_int
      else
        if (allocated(right_allocatable_holder%value)) then
          right => right_allocatable_holder%value
        else
          bound_right_status = 1_c_int
        end if
      end if
    case (4)
      right_holder_status = 0_c_int
      if (c_associated(bound_right)) then
        call c_f_pointer(bound_right, right_pointer_holder)
      else
        allocate(right_pointer_holder, stat=right_holder_status)
        nullify(right_pointer_holder%value)
        right_created = .true.
      end if
      if (right_holder_status /= 0_c_int) then
        bound_right_status = 4_c_int
      else
        if (associated(right_pointer_holder%value)) then
          right => right_pointer_holder%value
        else
          bound_right_status = 1_c_int
        end if
      end if
    case default
      bound_right_status = 6_c_int
    end select
    if (prik_derived_ready) then
      if (bound_left_status == 0_c_int) then
        select case (bound_left_access)
        case (5)
          bound_left_status = left_checkout_proc(left_transaction_address)
          if (bound_left_status == 0_c_int) then
            call c_f_pointer(left_transaction_address, left_allocatable_holder)
            left_acquired = .true.
          end if
        case (6)
          bound_left_status = left_checkout_proc(left_transaction_address)
          if (bound_left_status == 0_c_int) then
            call c_f_pointer(left_transaction_address, left_pointer_holder)
            left_acquired = .true.
          end if
        case default
        end select
        if (bound_left_status /= 0_c_int) then
          prik_derived_ready = .false.
        end if
      else
        prik_derived_ready = .false.
      end if
    end if
    if (prik_derived_ready) then
      if (bound_right_status == 0_c_int) then
        select case (bound_right_access)
        case (5)
          bound_right_status = right_checkout_proc(right_transaction_address)
          if (bound_right_status == 0_c_int) then
            call c_f_pointer(right_transaction_address, right_allocatable_holder)
            right_acquired = .true.
          end if
        case (6)
          bound_right_status = right_checkout_proc(right_transaction_address)
          if (bound_right_status == 0_c_int) then
            call c_f_pointer(right_transaction_address, right_pointer_holder)
            right_acquired = .true.
          end if
        case default
        end select
        if (bound_right_status /= 0_c_int) then
          prik_derived_ready = .false.
        end if
      else
        prik_derived_ready = .false.
      end if
    end if
    if (prik_derived_ready) then
      call prik_derived_step_0()
    end if
    if (right_acquired) then
      right_restore_status = right_restore_proc(right_transaction_address)
      if (right_restore_status /= 0_c_int) then
        bound_right_status = right_restore_status
      end if
      right_acquired = .false.
    end if
    if (left_acquired) then
      left_restore_status = left_restore_proc(left_transaction_address)
      if (left_restore_status /= 0_c_int) then
        bound_left_status = left_restore_status
      end if
      left_acquired = .false.
    end if
    if (left_created .and. bound_left_access == 3_c_int) then
      deallocate(left_allocatable_holder)
    end if
    if (left_created .and. bound_left_access == 4_c_int) then
      deallocate(left_pointer_holder)
    end if
    if (right_created .and. bound_right_access == 3_c_int) then
      deallocate(right_allocatable_holder)
    end if
    if (right_created .and. bound_right_access == 4_c_int) then
      deallocate(right_pointer_holder)
    end if
  contains
    subroutine prik_derived_step_0()
      if (bound_left_access == 2_c_int) then
        bound_left_status = left_scoped_proc(c_funloc(prik_derived_consumer_0), c_null_ptr)
      else
        call prik_derived_step_1()
      end if
    end subroutine prik_derived_step_0
    function prik_derived_consumer_0(address, context) result(status) bind(c)
      type(c_ptr), value :: address
      type(c_ptr), value :: context
      integer(c_int) :: status
      if (c_associated(address)) then
        call c_f_pointer(address, left)
        call prik_derived_step_1()
        status = 0_c_int
      else
        status = 1_c_int
      end if
    end function prik_derived_consumer_0
    subroutine prik_derived_step_1()
      if (bound_right_access == 2_c_int) then
        if (bound_left_access == 2_c_int .and. c_associated(bound_right_identity, bound_left_identity)) then
          right => left
          call prik_derived_step_2()
        else
          bound_right_status = right_scoped_proc(c_funloc(prik_derived_consumer_1), c_null_ptr)
        end if
      else
        call prik_derived_step_2()
      end if
    end subroutine prik_derived_step_1
    function prik_derived_consumer_1(address, context) result(status) bind(c)
      type(c_ptr), value :: address
      type(c_ptr), value :: context
      integer(c_int) :: status
      if (c_associated(address)) then
        call c_f_pointer(address, right)
        call prik_derived_step_2()
        status = 0_c_int
      else
        status = 1_c_int
      end if
    end function prik_derived_consumer_1
    subroutine prik_derived_step_2()
      result = c_null_ptr
      allocate(result_value, stat=prik_allocation_status)
      if (prik_allocation_status == 0) then
        select case (bound_left_polymorphic)
        case (1)
          result_value = left_polymorphic_1 + right
        case default
        end select
        result = c_loc(result_value)
      end if
    end subroutine prik_derived_step_2
  end function bind_c__prik_class_vector___add___0
  function bind_c__prik_overload_convert_0(value) result(result) bind(c, name="bind_c__prik_overload_convert_0")
    integer(c_int32_t), value :: value
    real(c_double) :: result
    result = native__prik_overload_convert_0(value)
  end function bind_c__prik_overload_convert_0
  function bind_c__prik_overload_convert_1(value) result(result) bind(c, name="bind_c__prik_overload_convert_1")
    real(c_double), value :: value
    integer(c_int32_t) :: result
    result = native__prik_overload_convert_1(value)
  end function bind_c__prik_overload_convert_1
  function bind_c_get_counter() result(result) bind(c, name="bind_c_get_counter")
    integer(c_int32_t) :: result
    result = native_counter
  end function bind_c_get_counter
  subroutine bind_c_set_counter(value) bind(c, name="bind_c_set_counter")
    integer(c_int32_t), value :: value
    native_counter = value
  end subroutine bind_c_set_counter
  function bind_c_workspace_allocated() result(result) bind(c, name="bind_c_workspace_allocated")
    logical(c_bool) :: result
    result = allocated(native_workspace)
  end function bind_c_workspace_allocated
  subroutine bind_c_workspace_array_actual(&
    & callback_address, &
    & context) bind(c, name="bind_c_workspace_array_actual")
    type(c_funptr), value :: callback_address
    type(c_ptr), value :: context
    procedure(prik_workspace_descriptor_consumer), pointer :: callback
    call c_f_procpointer(callback_address, callback)
    call callback(native_workspace, context)
  end subroutine bind_c_workspace_array_actual
  subroutine bind_c_workspace_deallocate() bind(c, name="bind_c_workspace_deallocate")
    if (allocated(native_workspace)) then
      deallocate(native_workspace)
    end if
  end subroutine bind_c_workspace_deallocate
  subroutine bind_c_workspace_descriptor(callback_address, context) bind(c, name="bind_c_workspace_descriptor")
    type(c_funptr), value :: callback_address
    type(c_ptr), value :: context
    procedure(prik_workspace_descriptor_consumer), pointer :: callback
    call c_f_procpointer(callback_address, callback)
    call callback(native_workspace, context)
  end subroutine bind_c_workspace_descriptor
  subroutine bind_c_workspace_resize(extent_0) bind(c, name="bind_c_workspace_resize")
    integer(c_int64_t), value :: extent_0
    if (allocated(native_workspace)) then
      deallocate(native_workspace)
    end if
    allocate(native_workspace(extent_0))
  end subroutine bind_c_workspace_resize
  subroutine bind_c_workspace_shape(extent_0) bind(c, name="bind_c_workspace_shape")
    integer(c_int64_t) :: extent_0
    if (allocated(native_workspace)) then
      extent_0 = size(native_workspace, 1, kind=c_int64_t)
    else
      extent_0 = 0_c_int64_t
    end if
  end subroutine bind_c_workspace_shape
  function bind_c_selected_array_actual() result(result) bind(c, name="bind_c_selected_array_actual")
    type(c_ptr) :: result
    if (associated(native_selected)) then
      result = c_loc(native_selected)
    else
      result = c_null_ptr
    end if
  end function bind_c_selected_array_actual
  subroutine bind_c_selected_associate(source) bind(c, name="bind_c_selected_associate")
    real(c_double), pointer, dimension(:), intent(in) :: source
    native_selected => source
  end subroutine bind_c_selected_associate
  function bind_c_selected_associated() result(result) bind(c, name="bind_c_selected_associated")
    logical(c_bool) :: result
    result = associated(native_selected)
  end function bind_c_selected_associated
  function bind_c_selected_contiguous() result(result) bind(c, name="bind_c_selected_contiguous")
    logical(c_bool) :: result
    result = .not. (associated(native_selected)) .or. is_contiguous(native_selected)
  end function bind_c_selected_contiguous
  subroutine bind_c_selected_descriptor(descriptor) bind(c, name="bind_c_selected_descriptor")
    real(c_double), pointer, dimension(:), intent(out) :: descriptor
    if (associated(native_selected)) then
      descriptor => native_selected
    else
      descriptor => null()
    end if
  end subroutine bind_c_selected_descriptor
  subroutine bind_c_selected_nullify() bind(c, name="bind_c_selected_nullify")
    native_selected => null()
  end subroutine bind_c_selected_nullify
  subroutine bind_c_selected_shape(extent_0) bind(c, name="bind_c_selected_shape")
    integer(c_int64_t) :: extent_0
    if (associated(native_selected)) then
      extent_0 = size(native_selected, 1, kind=c_int64_t)
    else
      extent_0 = 0_c_int64_t
    end if
  end subroutine bind_c_selected_shape
  function bind_c_prik_module_active_vector_present() &
    & result(result) bind(c, name="bind_c_prik_module_active_vector_present")
    logical(c_bool) :: result
    result = allocated(native_active_vector)
  end function bind_c_prik_module_active_vector_present
  function bind_c_prik_module_selected_vector_present() &
    & result(result) bind(c, name="bind_c_prik_module_selected_vector_present")
    logical(c_bool) :: result
    result = associated(native_selected_vector)
  end function bind_c_prik_module_selected_vector_present
  function bind_c_prik_field_holder_item_code_get(&
    & owner_address) result(result) bind(c, name="bind_c_prik_field_holder_item_code_get")
    type(c_ptr), value :: owner_address
    integer(c_int32_t) :: result
    type(prik_type_holder_item), pointer :: owner
    call c_f_pointer(owner_address, owner)
    result = owner%code
  end function bind_c_prik_field_holder_item_code_get
  subroutine bind_c_prik_field_holder_item_code_set(&
    & owner_address, &
    & value) bind(c, name="bind_c_prik_field_holder_item_code_set")
    type(c_ptr), value :: owner_address
    integer(c_int32_t), value :: value
    type(prik_type_holder_item), pointer :: owner
    call c_f_pointer(owner_address, owner)
    owner%code = value
  end subroutine bind_c_prik_field_holder_item_code_set
  function bind_c_prik_field_holder_item_weight_get(&
    & owner_address) result(result) bind(c, name="bind_c_prik_field_holder_item_weight_get")
    type(c_ptr), value :: owner_address
    real(c_double) :: result
    type(prik_type_holder_item), pointer :: owner
    call c_f_pointer(owner_address, owner)
    result = owner%weight
  end function bind_c_prik_field_holder_item_weight_get
  subroutine bind_c_prik_field_holder_item_weight_set(&
    & owner_address, &
    & value) bind(c, name="bind_c_prik_field_holder_item_weight_set")
    type(c_ptr), value :: owner_address
    real(c_double), value :: value
    type(prik_type_holder_item), pointer :: owner
    call c_f_pointer(owner_address, owner)
    owner%weight = value
  end subroutine bind_c_prik_field_holder_item_weight_set
  function bind_c_prik_field_vector_x_get(&
    & owner_address) result(result) bind(c, name="bind_c_prik_field_vector_x_get")
    type(c_ptr), value :: owner_address
    real(c_double) :: result
    type(prik_type_vector), pointer :: owner
    call c_f_pointer(owner_address, owner)
    result = owner%x
  end function bind_c_prik_field_vector_x_get
  subroutine bind_c_prik_field_vector_x_set(owner_address, value) bind(c, name="bind_c_prik_field_vector_x_set")
    type(c_ptr), value :: owner_address
    real(c_double), value :: value
    type(prik_type_vector), pointer :: owner
    call c_f_pointer(owner_address, owner)
    owner%x = value
  end subroutine bind_c_prik_field_vector_x_set
  function bind_c_prik_field_vector_y_get(&
    & owner_address) result(result) bind(c, name="bind_c_prik_field_vector_y_get")
    type(c_ptr), value :: owner_address
    real(c_double) :: result
    type(prik_type_vector), pointer :: owner
    call c_f_pointer(owner_address, owner)
    result = owner%y
  end function bind_c_prik_field_vector_y_get
  subroutine bind_c_prik_field_vector_y_set(owner_address, value) bind(c, name="bind_c_prik_field_vector_y_set")
    type(c_ptr), value :: owner_address
    real(c_double), value :: value
    type(prik_type_vector), pointer :: owner
    call c_f_pointer(owner_address, owner)
    owner%y = value
  end subroutine bind_c_prik_field_vector_y_set
  function bind_c_prik_field_handle_vector_samples_allocated(&
    & owner_address) result(result) bind(c, name="bind_c_prik_field_handle_vector_samples_allocated")
    type(c_ptr), value :: owner_address
    logical(c_bool) :: result
    type(prik_type_vector), pointer :: owner
    call c_f_pointer(owner_address, owner)
    result = allocated(owner%samples)
  end function bind_c_prik_field_handle_vector_samples_allocated
  subroutine bind_c_prik_field_handle_vector_samples_deallocate(&
    & owner_address) bind(c, name="bind_c_prik_field_handle_vector_samples_deallocate")
    type(c_ptr), value :: owner_address
    type(prik_type_vector), pointer :: owner
    call c_f_pointer(owner_address, owner)
    if (allocated(owner%samples)) then
      deallocate(owner%samples)
    end if
  end subroutine bind_c_prik_field_handle_vector_samples_deallocate
  subroutine bind_c_prik_field_handle_vector_samples_descriptor(&
    & owner_address, &
    & callback_address, &
    & context) bind(c, name="bind_c_prik_field_handle_vector_samples_descriptor")
    type(c_ptr), value :: owner_address
    type(c_funptr), value :: callback_address
    type(c_ptr), value :: context
    type(prik_type_vector), pointer :: owner
    procedure(prik_field_handle_vector_samples_consumer), pointer :: callback
    call c_f_pointer(owner_address, owner)
    call c_f_procpointer(callback_address, callback)
    call callback(owner%samples, context)
  end subroutine bind_c_prik_field_handle_vector_samples_descriptor
  subroutine bind_c_prik_field_handle_vector_samples_resize(&
    & owner_address, &
    & extent_0) bind(c, name="bind_c_prik_field_handle_vector_samples_resize")
    type(c_ptr), value :: owner_address
    integer(c_int64_t), value :: extent_0
    type(prik_type_vector), pointer :: owner
    call c_f_pointer(owner_address, owner)
    if (allocated(owner%samples)) then
      deallocate(owner%samples)
    end if
    allocate(owner%samples(extent_0))
  end subroutine bind_c_prik_field_handle_vector_samples_resize
  subroutine bind_c_prik_field_handle_vector_samples_shape(&
    & owner_address, &
    & extent_0) bind(c, name="bind_c_prik_field_handle_vector_samples_shape")
    type(c_ptr), value :: owner_address
    integer(c_int64_t) :: extent_0
    type(prik_type_vector), pointer :: owner
    call c_f_pointer(owner_address, owner)
    if (allocated(owner%samples)) then
      extent_0 = size(owner%samples, 1, kind=c_int64_t)
    else
      extent_0 = 0_c_int64_t
    end if
  end subroutine bind_c_prik_field_handle_vector_samples_shape
  function bind_c_prik_module_field_active_vector_x_get() &
    & result(result) bind(c, name="bind_c_prik_module_field_active_vector_x_get")
    real(c_double) :: result
    result = native_active_vector%x
  end function bind_c_prik_module_field_active_vector_x_get
  subroutine bind_c_prik_module_field_active_vector_x_set(&
    & value) bind(c, name="bind_c_prik_module_field_active_vector_x_set")
    real(c_double), value :: value
    native_active_vector%x = value
  end subroutine bind_c_prik_module_field_active_vector_x_set
  function bind_c_prik_module_field_active_vector_y_get() &
    & result(result) bind(c, name="bind_c_prik_module_field_active_vector_y_get")
    real(c_double) :: result
    result = native_active_vector%y
  end function bind_c_prik_module_field_active_vector_y_get
  subroutine bind_c_prik_module_field_active_vector_y_set(&
    & value) bind(c, name="bind_c_prik_module_field_active_vector_y_set")
    real(c_double), value :: value
    native_active_vector%y = value
  end subroutine bind_c_prik_module_field_active_vector_y_set
  function bind_c_prik_module_field_handle_active_vector_samples_allocated() &
    & result(result) bind(c, name="bind_c_prik_module_field_handle_active_vector_samples_allocated")
    logical(c_bool) :: result
    result = allocated(native_active_vector%samples)
  end function bind_c_prik_module_field_handle_active_vector_samples_allocated
  subroutine bind_c_prik_module_field_handle_active_vector_samples_deallocate() &
    & bind(c, name="bind_c_prik_module_field_handle_active_vector_samples_deallocate")
    if (allocated(native_active_vector%samples)) then
      deallocate(native_active_vector%samples)
    end if
  end subroutine bind_c_prik_module_field_handle_active_vector_samples_deallocate
  subroutine bind_c_prik_module_field_handle_active_vector_samples_descriptor(&
    & callback_address, &
    & context) bind(c, name="bind_c_prik_module_field_handle_active_vector_samples_descriptor")
    type(c_funptr), value :: callback_address
    type(c_ptr), value :: context
    procedure(prik_module_field_handle_active_vector_samples_consumer), pointer :: callback
    call c_f_procpointer(callback_address, callback)
    call callback(native_active_vector%samples, context)
  end subroutine bind_c_prik_module_field_handle_active_vector_samples_descriptor
  subroutine bind_c_prik_module_field_handle_active_vector_samples_resize(&
    & extent_0) bind(c, name="bind_c_prik_module_field_handle_active_vector_samples_resize")
    integer(c_int64_t), value :: extent_0
    if (allocated(native_active_vector%samples)) then
      deallocate(native_active_vector%samples)
    end if
    allocate(native_active_vector%samples(extent_0))
  end subroutine bind_c_prik_module_field_handle_active_vector_samples_resize
  subroutine bind_c_prik_module_field_handle_active_vector_samples_shape(&
    & extent_0) bind(c, name="bind_c_prik_module_field_handle_active_vector_samples_shape")
    integer(c_int64_t) :: extent_0
    if (allocated(native_active_vector%samples)) then
      extent_0 = size(native_active_vector%samples, 1, kind=c_int64_t)
    else
      extent_0 = 0_c_int64_t
    end if
  end subroutine bind_c_prik_module_field_handle_active_vector_samples_shape
  function bind_c_prik_module_field_selected_vector_x_get() &
    & result(result) bind(c, name="bind_c_prik_module_field_selected_vector_x_get")
    real(c_double) :: result
    result = native_selected_vector%x
  end function bind_c_prik_module_field_selected_vector_x_get
  subroutine bind_c_prik_module_field_selected_vector_x_set(&
    & value) bind(c, name="bind_c_prik_module_field_selected_vector_x_set")
    real(c_double), value :: value
    native_selected_vector%x = value
  end subroutine bind_c_prik_module_field_selected_vector_x_set
  function bind_c_prik_module_field_selected_vector_y_get() &
    & result(result) bind(c, name="bind_c_prik_module_field_selected_vector_y_get")
    real(c_double) :: result
    result = native_selected_vector%y
  end function bind_c_prik_module_field_selected_vector_y_get
  subroutine bind_c_prik_module_field_selected_vector_y_set(&
    & value) bind(c, name="bind_c_prik_module_field_selected_vector_y_set")
    real(c_double), value :: value
    native_selected_vector%y = value
  end subroutine bind_c_prik_module_field_selected_vector_y_set
  function bind_c_prik_module_field_handle_selected_vector_samples_allocated() &
    & result(result) bind(c, name="bind_c_prik_module_field_handle_selected_vector_samples_allocated")
    logical(c_bool) :: result
    result = allocated(native_selected_vector%samples)
  end function bind_c_prik_module_field_handle_selected_vector_samples_allocated
  subroutine bind_c_prik_module_field_handle_selected_vector_samples_deallocate() &
    & bind(c, name="bind_c_prik_module_field_handle_selected_vector_samples_deallocate")
    if (allocated(native_selected_vector%samples)) then
      deallocate(native_selected_vector%samples)
    end if
  end subroutine bind_c_prik_module_field_handle_selected_vector_samples_deallocate
  subroutine bind_c_prik_module_field_handle_selected_vector_samples_descriptor(&
    & callback_address, &
    & context) bind(c, name="bind_c_prik_module_field_handle_selected_vector_samples_descriptor")
    type(c_funptr), value :: callback_address
    type(c_ptr), value :: context
    procedure(prik_module_field_handle_selected_vector_samples_consumer), pointer :: callback
    call c_f_procpointer(callback_address, callback)
    call callback(native_selected_vector%samples, context)
  end subroutine bind_c_prik_module_field_handle_selected_vector_samples_descriptor
  subroutine bind_c_prik_module_field_handle_selected_vector_samples_resize(&
    & extent_0) bind(c, name="bind_c_prik_module_field_handle_selected_vector_samples_resize")
    integer(c_int64_t), value :: extent_0
    if (allocated(native_selected_vector%samples)) then
      deallocate(native_selected_vector%samples)
    end if
    allocate(native_selected_vector%samples(extent_0))
  end subroutine bind_c_prik_module_field_handle_selected_vector_samples_resize
  subroutine bind_c_prik_module_field_handle_selected_vector_samples_shape(&
    & extent_0) bind(c, name="bind_c_prik_module_field_handle_selected_vector_samples_shape")
    integer(c_int64_t) :: extent_0
    if (allocated(native_selected_vector%samples)) then
      extent_0 = size(native_selected_vector%samples, 1, kind=c_int64_t)
    else
      extent_0 = 0_c_int64_t
    end if
  end subroutine bind_c_prik_module_field_handle_selected_vector_samples_shape
  function bind_c_prik_allocatable_holder_field_holder_item_code_get(&
    & owner_address) result(result) bind(c, name="bind_c_prik_allocatable_holder_field_holder_item_code_get")
    type(c_ptr), value :: owner_address
    integer(c_int32_t) :: result
    type(prik_holder_item_allocatable_holder), pointer :: owner
    call c_f_pointer(owner_address, owner)
    result = owner%value%code
  end function bind_c_prik_allocatable_holder_field_holder_item_code_get
  subroutine bind_c_prik_allocatable_holder_field_holder_item_code_set(&
    & owner_address, &
    & value) bind(c, name="bind_c_prik_allocatable_holder_field_holder_item_code_set")
    type(c_ptr), value :: owner_address
    integer(c_int32_t), value :: value
    type(prik_holder_item_allocatable_holder), pointer :: owner
    call c_f_pointer(owner_address, owner)
    owner%value%code = value
  end subroutine bind_c_prik_allocatable_holder_field_holder_item_code_set
  function bind_c_prik_allocatable_holder_field_holder_item_weight_get(&
    & owner_address) result(result) bind(c, name="bind_c_prik_allocatable_holder_field_holder_item_weight_get")
    type(c_ptr), value :: owner_address
    real(c_double) :: result
    type(prik_holder_item_allocatable_holder), pointer :: owner
    call c_f_pointer(owner_address, owner)
    result = owner%value%weight
  end function bind_c_prik_allocatable_holder_field_holder_item_weight_get
  subroutine bind_c_prik_allocatable_holder_field_holder_item_weight_set(&
    & owner_address, &
    & value) bind(c, name="bind_c_prik_allocatable_holder_field_holder_item_weight_set")
    type(c_ptr), value :: owner_address
    real(c_double), value :: value
    type(prik_holder_item_allocatable_holder), pointer :: owner
    call c_f_pointer(owner_address, owner)
    owner%value%weight = value
  end subroutine bind_c_prik_allocatable_holder_field_holder_item_weight_set
  function bind_c_prik_pointer_holder_field_holder_item_code_get(&
    & owner_address) result(result) bind(c, name="bind_c_prik_pointer_holder_field_holder_item_code_get")
    type(c_ptr), value :: owner_address
    integer(c_int32_t) :: result
    type(prik_holder_item_pointer_holder), pointer :: owner
    call c_f_pointer(owner_address, owner)
    result = owner%value%code
  end function bind_c_prik_pointer_holder_field_holder_item_code_get
  subroutine bind_c_prik_pointer_holder_field_holder_item_code_set(&
    & owner_address, &
    & value) bind(c, name="bind_c_prik_pointer_holder_field_holder_item_code_set")
    type(c_ptr), value :: owner_address
    integer(c_int32_t), value :: value
    type(prik_holder_item_pointer_holder), pointer :: owner
    call c_f_pointer(owner_address, owner)
    owner%value%code = value
  end subroutine bind_c_prik_pointer_holder_field_holder_item_code_set
  function bind_c_prik_pointer_holder_field_holder_item_weight_get(&
    & owner_address) result(result) bind(c, name="bind_c_prik_pointer_holder_field_holder_item_weight_get")
    type(c_ptr), value :: owner_address
    real(c_double) :: result
    type(prik_holder_item_pointer_holder), pointer :: owner
    call c_f_pointer(owner_address, owner)
    result = owner%value%weight
  end function bind_c_prik_pointer_holder_field_holder_item_weight_get
  subroutine bind_c_prik_pointer_holder_field_holder_item_weight_set(&
    & owner_address, &
    & value) bind(c, name="bind_c_prik_pointer_holder_field_holder_item_weight_set")
    type(c_ptr), value :: owner_address
    real(c_double), value :: value
    type(prik_holder_item_pointer_holder), pointer :: owner
    call c_f_pointer(owner_address, owner)
    owner%value%weight = value
  end subroutine bind_c_prik_pointer_holder_field_holder_item_weight_set
  function bind_c_prik_create_holder_item() result(result) bind(c, name="bind_c_prik_create_holder_item")
    type(c_ptr) :: result
    type(prik_type_holder_item), pointer :: value
    integer(c_int) :: allocation_status
    result = c_null_ptr
    allocate(value, stat=allocation_status)
    if (allocation_status == 0_c_int) then
      result = c_loc(value)
    end if
  end function bind_c_prik_create_holder_item
  function bind_c_prik_create_vector() result(result) bind(c, name="bind_c_prik_create_vector")
    type(c_ptr) :: result
    type(prik_type_vector), pointer :: value
    integer(c_int) :: allocation_status
    result = c_null_ptr
    allocate(value, stat=allocation_status)
    if (allocation_status == 0_c_int) then
      result = c_loc(value)
    end if
  end function bind_c_prik_create_vector
  subroutine bind_c_prik_destroy_holder_item(address) bind(c, name="bind_c_prik_destroy_holder_item")
    type(c_ptr), value :: address
    type(prik_type_holder_item), pointer :: value
    call c_f_pointer(address, value)
    if (associated(value)) then
      deallocate(value)
    end if
  end subroutine bind_c_prik_destroy_holder_item
  subroutine bind_c_prik_destroy_vector(address) bind(c, name="bind_c_prik_destroy_vector")
    type(c_ptr), value :: address
    type(prik_type_vector), pointer :: value
    call c_f_pointer(address, value)
    if (associated(value)) then
      deallocate(value)
    end if
  end subroutine bind_c_prik_destroy_vector
  subroutine bind_c_prik_destroy_holder_item_allocatable_holder(&
    & address) bind(c, name="bind_c_prik_destroy_holder_item_allocatable_holder")
    type(c_ptr), value :: address
    type(prik_holder_item_allocatable_holder), pointer :: holder
    call c_f_pointer(address, holder)
    if (associated(holder)) then
      deallocate(holder)
    end if
  end subroutine bind_c_prik_destroy_holder_item_allocatable_holder
  subroutine bind_c_prik_destroy_vector_allocatable_holder(&
    & address) bind(c, name="bind_c_prik_destroy_vector_allocatable_holder")
    type(c_ptr), value :: address
    type(prik_vector_allocatable_holder), pointer :: holder
    call c_f_pointer(address, holder)
    if (associated(holder)) then
      deallocate(holder)
    end if
  end subroutine bind_c_prik_destroy_vector_allocatable_holder
  function bind_c_prik_holder_item_allocatable_holder_present(&
    & address) result(result) bind(c, name="bind_c_prik_holder_item_allocatable_holder_present")
    type(c_ptr), value :: address
    logical(c_bool) :: result
    type(prik_holder_item_allocatable_holder), pointer :: holder
    call c_f_pointer(address, holder)
    result = allocated(holder%value)
  end function bind_c_prik_holder_item_allocatable_holder_present
  function bind_c_prik_vector_allocatable_holder_present(&
    & address) result(result) bind(c, name="bind_c_prik_vector_allocatable_holder_present")
    type(c_ptr), value :: address
    logical(c_bool) :: result
    type(prik_vector_allocatable_holder), pointer :: holder
    call c_f_pointer(address, holder)
    result = allocated(holder%value)
  end function bind_c_prik_vector_allocatable_holder_present
  subroutine bind_c_prik_destroy_holder_item_pointer_holder(&
    & address) bind(c, name="bind_c_prik_destroy_holder_item_pointer_holder")
    type(c_ptr), value :: address
    type(prik_holder_item_pointer_holder), pointer :: holder
    call c_f_pointer(address, holder)
    if (associated(holder)) then
      nullify(holder%value)
      deallocate(holder)
    end if
  end subroutine bind_c_prik_destroy_holder_item_pointer_holder
  subroutine bind_c_prik_destroy_vector_pointer_holder(&
    & address) bind(c, name="bind_c_prik_destroy_vector_pointer_holder")
    type(c_ptr), value :: address
    type(prik_vector_pointer_holder), pointer :: holder
    call c_f_pointer(address, holder)
    if (associated(holder)) then
      nullify(holder%value)
      deallocate(holder)
    end if
  end subroutine bind_c_prik_destroy_vector_pointer_holder
  function bind_c_prik_holder_item_pointer_holder_present(&
    & address) result(result) bind(c, name="bind_c_prik_holder_item_pointer_holder_present")
    type(c_ptr), value :: address
    logical(c_bool) :: result
    type(prik_holder_item_pointer_holder), pointer :: holder
    call c_f_pointer(address, holder)
    result = associated(holder%value)
  end function bind_c_prik_holder_item_pointer_holder_present
  function bind_c_prik_vector_pointer_holder_present(&
    & address) result(result) bind(c, name="bind_c_prik_vector_pointer_holder_present")
    type(c_ptr), value :: address
    logical(c_bool) :: result
    type(prik_vector_pointer_holder), pointer :: holder
    call c_f_pointer(address, holder)
    result = associated(holder%value)
  end function bind_c_prik_vector_pointer_holder_present
  function bind_c_prik_origin_active_vector_26504a12_present() &
    & result(result) bind(c, name="bind_c_prik_origin_active_vector_26504a12_present")
    logical(c_bool) :: result
    result = allocated(native_active_vector)
  end function bind_c_prik_origin_active_vector_26504a12_present
  function bind_c_prik_origin_active_vector_26504a12_scoped(&
    & consumer, &
    & context) result(status) bind(c, name="bind_c_prik_origin_active_vector_26504a12_scoped")
    type(c_funptr), value :: consumer
    type(c_ptr), value :: context
    integer(c_int) :: status
    procedure(prik_derived_consumer), pointer :: consume
    call c_f_procpointer(consumer, consume)
    status = 1_c_int
    if (allocated(native_active_vector)) then
      status = prik_invoke_origin(native_active_vector)
    end if
  contains
    function prik_invoke_origin(value) result(inner_status)
      type(prik_type_vector), target :: value
      integer(c_int) :: inner_status
      inner_status = consume(c_loc(value), context)
    end function prik_invoke_origin
  end function bind_c_prik_origin_active_vector_26504a12_scoped
  function bind_c_prik_origin_active_vector_26504a12_checkout(&
    & holder_address) result(status) bind(c, name="bind_c_prik_origin_active_vector_26504a12_checkout")
    type(c_ptr), intent(out) :: holder_address
    integer(c_int) :: status
    type(prik_vector_allocatable_holder), pointer :: holder
    integer(c_int) :: allocation_status
    holder_address = c_null_ptr
    allocate(holder, stat=allocation_status)
    if (allocation_status == 0_c_int) then
      call move_alloc(native_active_vector, holder%value)
      holder_address = c_loc(holder)
      status = 0_c_int
    else
      status = 4_c_int
    end if
  end function bind_c_prik_origin_active_vector_26504a12_checkout
  function bind_c_prik_origin_active_vector_26504a12_restore(&
    & holder_address) result(status) bind(c, name="bind_c_prik_origin_active_vector_26504a12_restore")
    type(c_ptr), value :: holder_address
    integer(c_int) :: status
    type(prik_vector_allocatable_holder), pointer :: holder
    call c_f_pointer(holder_address, holder)
    if (associated(holder)) then
      call move_alloc(holder%value, native_active_vector)
      deallocate(holder)
      status = 0_c_int
    else
      status = 5_c_int
    end if
  end function bind_c_prik_origin_active_vector_26504a12_restore
  function bind_c_prik_origin_selected_vector_d2fd3c9d_present() &
    & result(result) bind(c, name="bind_c_prik_origin_selected_vector_d2fd3c9d_present")
    logical(c_bool) :: result
    result = associated(native_selected_vector)
  end function bind_c_prik_origin_selected_vector_d2fd3c9d_present
  function bind_c_prik_origin_selected_vector_d2fd3c9d_scoped(&
    & consumer, &
    & context) result(status) bind(c, name="bind_c_prik_origin_selected_vector_d2fd3c9d_scoped")
    type(c_funptr), value :: consumer
    type(c_ptr), value :: context
    integer(c_int) :: status
    procedure(prik_derived_consumer), pointer :: consume
    call c_f_procpointer(consumer, consume)
    status = 1_c_int
    if (associated(native_selected_vector)) then
      status = prik_invoke_origin(native_selected_vector)
    end if
  contains
    function prik_invoke_origin(value) result(inner_status)
      type(prik_type_vector), target :: value
      integer(c_int) :: inner_status
      inner_status = consume(c_loc(value), context)
    end function prik_invoke_origin
  end function bind_c_prik_origin_selected_vector_d2fd3c9d_scoped
  function bind_c_prik_origin_selected_vector_d2fd3c9d_checkout(&
    & holder_address) result(status) bind(c, name="bind_c_prik_origin_selected_vector_d2fd3c9d_checkout")
    type(c_ptr), intent(out) :: holder_address
    integer(c_int) :: status
    type(prik_vector_pointer_holder), pointer :: holder
    integer(c_int) :: allocation_status
    holder_address = c_null_ptr
    allocate(holder, stat=allocation_status)
    if (allocation_status == 0_c_int) then
      if (associated(native_selected_vector)) then
        holder%value => native_selected_vector
      else
        nullify(holder%value)
      end if
      nullify(native_selected_vector)
      holder_address = c_loc(holder)
      status = 0_c_int
    else
      status = 4_c_int
    end if
  end function bind_c_prik_origin_selected_vector_d2fd3c9d_checkout
  function bind_c_prik_origin_selected_vector_d2fd3c9d_restore(&
    & holder_address) result(status) bind(c, name="bind_c_prik_origin_selected_vector_d2fd3c9d_restore")
    type(c_ptr), value :: holder_address
    integer(c_int) :: status
    type(prik_vector_pointer_holder), pointer :: holder
    call c_f_pointer(holder_address, holder)
    if (associated(holder)) then
      if (associated(holder%value)) then
        native_selected_vector => holder%value
      else
        nullify(native_selected_vector)
      end if
      nullify(holder%value)
      deallocate(holder)
      status = 0_c_int
    else
      status = 5_c_int
    end if
  end function bind_c_prik_origin_selected_vector_d2fd3c9d_restore
end module bind_c_refactoring_goldens_wrapper
function prik_callback_adapter_callback_83b3d1d9(value) result(callback_result)
  use iso_c_binding, only: c_double, c_loc, c_ptr
  implicit none
  real(c_double), intent(in) :: value
  real(c_double) :: callback_result
  type(c_ptr) :: value_data
  real(c_double), target :: value_callback_storage
  interface
    function prik_callback_trampoline_callback_83b3d1d9_call(&
      & value_data) bind(c, name="prik_callback_trampoline_callback_83b3d1d9") result(callback_result)
      import :: c_ptr, c_double
      type(c_ptr), value :: value_data
      real(c_double) :: callback_result
    end function prik_callback_trampoline_callback_83b3d1d9_call
  end interface
  value_callback_storage = value
  value_data = c_loc(value_callback_storage)
  callback_result = prik_callback_trampoline_callback_83b3d1d9_call(value_data)
end function prik_callback_adapter_callback_83b3d1d9