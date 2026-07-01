<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

<template>
  <section class="placeholder-page">
    <h1>{{ title }}</h1>
    <p>{{ description }}</p>
  </section>
</template>
