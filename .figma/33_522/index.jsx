import React from 'react';

import styles from './index.module.scss';

const Component = () => {
  return (
    <div className={styles.thumbnail}>
      <div className={styles.autoWrapper}>
        <div className={styles.title}>
          <p className={styles.newEraEnergy}>New Era Energy</p>
          <p className={styles.iCraftAModernSustain}>
            I craft a modern, sustainable energy experience for the New Energy
            website, featuring high-quality images of renewable tech, a minimalistic
            green and white color scheme, and well-organized sections showcasing
            services and our commitment to a greener future.
          </p>
        </div>
        <div className={styles.by}>
          <img src="../image/mnbhdm0e-j79mlvm.png" className={styles.a106577170} />
          <p className={styles.peterPontocom}>Peter Pontocom</p>
        </div>
      </div>
      <div className={styles.autoWrapper2}>
        <div className={styles.asset}>
          <div className={styles.home3} />
          <div className={styles.home2} />
        </div>
        <div className={styles.eventNlwJourney} />
      </div>
    </div>
  );
}

export default Component;
