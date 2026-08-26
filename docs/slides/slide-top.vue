<script setup>
import { useSlideContext } from '@slidev/client'

const { $page, $nav } = useSlideContext()
</script>

<template>
  <div v-if="$page > 1" class="slide-no">
    {{ $page }} / {{ $nav.total }}
  </div>
</template>

<style scoped>
.slide-no {
  position: absolute;
  right: 1.1rem;
  bottom: 0.7rem;
  font-family: var(--slidev-code-font-family, monospace);
  font-size: 0.7rem;
  opacity: 0.35;
  pointer-events: none;
}
</style>
