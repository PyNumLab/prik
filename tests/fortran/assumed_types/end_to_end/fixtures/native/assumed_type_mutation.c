#include <stdint.h>
#include <ISO_Fortran_binding.h>

void bump_address(void *x)
{
    ((int64_t *)x)[0] += 1;
}

void bump_descriptor(CFI_cdesc_t *x)
{
    int64_t *first = (int64_t *)x->base_addr;
    int64_t *last = (int64_t *)((char *)x->base_addr + (x->dim[0].extent - 1) * x->dim[0].sm);
    *first += 1;
    *last += 1;
}

void bump_scalar(void *x)
{
    *(int64_t *)x += 1;
}
