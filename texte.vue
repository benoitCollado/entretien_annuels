     <div role="radiogroup" :aria-labelledby="identifiant" class="flex flex-wrap gap-2">
       <button
         v-for="valeur in echelle"
         :key="valeur"
         type="button"
         role="radio"
         :aria-checked="note === valeur"
         :disabled="!modifiable"
         class="h-10 w-10 rounded-full border text-sm font-medium disabled:opacity-50"
         @click="emet('saisir', note === valeur ? null : { note: valeur })"
       >
         {{ valeur }}
       </button>
     </div>

        add_header X-Content-Type-Options "nosniff" always;
   add_header X-Frame-Options "DENY" always;
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;

