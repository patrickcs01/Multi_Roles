import numpy as np
import tensorflow as tf
import pdb
import Multi_Roles_Model

# reproducible
np.random.seed(1)
tf.set_random_seed(1)


class PolicyGradient:
    def __init__(
            self,
            config,
            vocab,
            output_graph=False,
    ):
        self.config = config
        self.vocab = vocab
        self.lr = config.learn_rate
        self.gamma = config.reward_decay

        self.ep_obs, self.ep_as, self.ep_rs = [], [], []
        self.sess = tf.Session()
        self._build_net()

        if output_graph:
            # $ tensorboard --logdir=logs
            # http://0.0.0.0:6006/
            # tf.train.SummaryWriter soon be deprecated, use following
            tf.summary.FileWriter("logs/", self.sess.graph)

    def _build_net(self):
        print('establish the model...')
        self.model = Multi_Roles_Model.MuliRolesModel(self.config, self.vocab)

        print('Reload model from checkpoints.....')
        ckpt = tf.train.get_checkpoint_state(self.config.checkpoints_dir)
        self.model.saver.restore(self.sess, ckpt.model_checkpoint_path)

    def choose_action(self, observation):
        loss, predict, _ = self.model.step(self.sess, observation, step_type='test')

        return predict

    def store_transition(self, s, a, r):
        self.ep_obs.append(s)  # observations
        self.ep_as.append(a)  # actions
        self.ep_rs.append(r)  # rewards

    def learn(self):
        # discount and normalize episode reward
        discounted_ep_rs_norm = self._discount_and_norm_rewards()

        # train on episode
        for index,conversation in enumerate(self.ep_obs):
            conversation['answer']=self.ep_as[index]
            loss, _, _ = self.model.step(self.sess, conversation, self.ep_rs[index], step_type='rl')

        self.ep_obs, self.ep_as, self.ep_rs = [], [], []  # empty episode data
        return discounted_ep_rs_norm

    def _discount_and_norm_rewards(self):
        # discount episode rewards
        discounted_ep_rs = np.zeros_like(self.ep_rs)
        running_add = 0
        for t in reversed(range(0, len(self.ep_rs))):
            running_add = running_add * self.gamma + self.ep_rs[t]
            discounted_ep_rs[t] = running_add

        # normalize episode rewards
        # pdb.set_trace()
        discounted_ep_rs -= np.mean(discounted_ep_rs)
        discounted_ep_rs /= np.std(discounted_ep_rs)
        return discounted_ep_rs
