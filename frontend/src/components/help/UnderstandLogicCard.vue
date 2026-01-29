<template>
  <v-card class="mb-6 card-understand" variant="outlined" rounded="lg">
    <v-card-title class="d-flex align-center"><span>Understand the logic</span></v-card-title>
    <v-card-text class="text-caption">
      <div class="mb-2">
        <strong>Correlations</strong> – “How strongly do two columns move together?”
        <br />
        Example: <code>units_sold</code> vs <code>marketing_spend</code>.
      </div>
      <div class="mb-2">
        <strong>Crosstabs</strong> – “How does the mix of categories change across another field?”
      </div>
      <div class="mb-2"><strong>Key Drivers</strong> – “Which columns help explain my main metric?”</div>
      <div class="mb-2"><strong>Outliers</strong> – “What values look unusually high or low?”</div>
      <div class="mb-2"><strong>Summary Stats</strong> – “What does the distribution look like?”</div>
      <div><strong>Time Series</strong> – “How does this metric move over time?”</div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
// Presentational card only (no state).
</script>