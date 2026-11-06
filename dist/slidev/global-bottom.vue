<template>
  <!-- The number is a sticker of the note colour and the bar above it shows how far the deck
       is. Both stay off the opening slide, the closing one and a slide that carries one number,
       where the composition speaks alone. The whole condition sits in the template: reading the
       context in a setup block stops an export, because the print page renders this layer
       outside the provider the composable expects -->
  <div
    v-if="
      $slidev.nav.currentPage > 1 &&
      $slidev.nav.currentPage < $slidev.nav.total &&
      !['cover', 'links', 'end'].includes($slidev.nav.currentLayout)
    "
    class="ddlc-chrome"
  >
    <div class="ddlc-progress">
      <div
        :style="{
          width: `${Math.round(($slidev.nav.currentPage / $slidev.nav.total) * 100)}%`,
        }"
      />
    </div>
    <div v-if="$slidev.nav.currentLayout !== 'fact'" class="ddlc-page">
      {{ $slidev.nav.currentPage }} / {{ $slidev.nav.total }}
    </div>
  </div>
</template>
