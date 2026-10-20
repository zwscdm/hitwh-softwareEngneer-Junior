package edu.hitwh.context;

import edu.hitwh.utils.MyTools;

import java.lang.reflect.InvocationTargetException;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 自定义框架的核心类
 */
public class AnnotationConfigApplicationContext {

    // 原材料集合：存放所有的标注有@Component的类的信息
    private Set<BeanDefination> beanDefinations = new HashSet<>();
    // IOC 容器，单例池
    private Map<String, Object> singletonObjects = new ConcurrentHashMap<>();

    /**
     * 利用构造函数初始化。
     * 实验一：根据注解解决包扫描问题 ：Set<BeanDefination> findBeanDefinations(String packageToScan)
     * 实验二：根据原材料 beanDefinations 创建bean： void createObject(Set<BeanDefination> beanDefinations)
     * 实验三：实现对象的自动装配 autoWireObject(Set<BeanDefination> beanDefinations)
     * 实验四：将之上的三个方法重构，使其具有灵活性。
     *
     * @param packageToScan 待扫描的包
     */
    public AnnotationConfigApplicationContext(String packageToScan) throws InvocationTargetException, NoSuchMethodException, InstantiationException, IllegalAccessException {
        // exp01： 实验一：遍历 pageToScan，找到目标类
        beanDefinations = findBeanDefinations(packageToScan);
        // ex02：实验二：将 BeanDefinations 的信息取出，构建出 Bean容器
        createObject(beanDefinations);
        // ex03 新增部分：对象的自动装配
        autoWireObject(beanDefinations);
    }

    /**
     * 找到所有classpath下标注了@Component的类的信息，并存储在一个集合中。
     * 算法思路：
     * 1. 利用工具类 MyTools.getgetClasses(String packageToScan) 获取packageToScan下所有的 .class文件，即形成所有的class对象，
     * 获得一个 classes 集合；注意：使用集合的主要原因是，集合中没有重复的值。
     * 2. 遍历classes集合，判断每一个class对象是否有@Component注解,获取所有标注@Component注解的class对象及其名字，
     * 存放到beanDefinations中，方便 实验2 中对其进行实例化。
     * <p>
     * 2.1 从集合中拿出一个class对象，假设命名为 clazz
     * 2.2 如果 class对象上有注解@Component,说明该class对象是我们自定义框架管理的Bean。那么就获取@Component的 value 属性，
     * 2.2.1 如果 value属性=“”，也就是value的默认值，那么，该 Bean 的名字应该是：不包括包的类名，并且要把类名首字母变小写。
     * 2.2.2 否则类名就是@Component注解的value值
     * 2.2.3 现在构建出BeanDefination对象，还缺scope值。因此，判断类名上有没有标注@Scope。
     * 如果有，拿到该scope注解对象后，获取其value的值，scope=该值；
     * 如果没有标注 @Scope，那么就表示你的框架中，默认scope的值为 “singleton”，表示该类为单例。
     * <p>
     * 2.2.4 现在，有了BeanName，有了Class对象，有了scope的值，因此可以产生一个BeanDefination对象，并且将该信息添加到 beanDefinations中。
     * 3. 返回 beanDefinations
     *
     * @param packageToScan 待扫描的包
     * @return 包下所有带 @Component注解的类的信息的集合
     */
    private Set<BeanDefination> findBeanDefinations(String packageToScan) {
        // 1. 获取包下的所有的类
        Set<Class<?>> classes = MyTools.getClasses(packageToScan);

        // 2. 遍历classes集合，判断是否有@Component注解
        for (Class<?> clazz : classes) {
            // 检查是否有@Component注解
            if (clazz.isAnnotationPresent(Component.class)) {
                // 获取@Component注解
                Component component = clazz.getAnnotation(Component.class);

                // 获取beanName
                String beanName;
                String value = component.value();

                // 判断value是否为空
                if (value == null || value.isEmpty()) {
                    // 获取简单类名（不包含包名）
                    String className = clazz.getSimpleName();
                    // 首字母小写
                    beanName = className.substring(0, 1).toLowerCase()
                            + className.substring(1);
                } else {
                    beanName = value;
                }

// 新增：获取scope值
                String scope = "singleton"; // 默认值
                if (clazz.isAnnotationPresent(Scope.class)) {
                    Scope scopeAnnotation = clazz.getAnnotation(Scope.class);
                    scope = scopeAnnotation.value();
                }

// 修改：创建BeanDefinition对象，传入scope参数
                BeanDefination bd = new BeanDefination(beanName, clazz, scope);
                // 添加到集合中
                beanDefinations.add(bd);

                // 可以打印日志（可选）
                System.out.println("找到Bean: " + beanName + " -> " + clazz.getName());
            }
        }

        return beanDefinations;
    }

    /**
     * 该私有方法的功能：遍历beanDefinations，取出每个beanDefination，根据其beanClass属性值，生成Bean对象，并将Bean对象放入单例池
     * <p>
     * 具体算法如下：
     * 1.获取beanDefinations的迭代器iterator
     * 2 利用iterator遍历beanDefinations集合
     * 2.1 取出集合中的一个 beanDefination对象。
     * 2.2 获取该对象的属性值 beanName、beanClass和 scope
     * 2.3 判断sope的值是否是“singleton”，如果是，将产生的对象放到单例池子。不是单例的不管。
     * 2.3.1 利用beanClass的 getDeclaredConstructor().newInstance()，获取Bean对象。
     * 2.3.2 将该Bean对象放入 singletonObjects 这个map<String,Object>中，String是指beanName，Object是指Bean对象。
     *
     * @param beanDefinations 所有标注了@Component注解的类的集合，又称为原材料集合。
     */

    private void createObject(Set<BeanDefination> beanDefinations) throws NoSuchMethodException, InvocationTargetException, InstantiationException, IllegalAccessException {
        // 1. 遍历所有图纸（BeanDefinition）
        for (BeanDefination bd : beanDefinations) {
            String beanName = bd.getBeanName();
            Class beanClass = bd.getBeanClass();
            String scope = bd.getScope();  // 从BeanDefinition中获取

            // 2. 检查是不是单例
            if ("singleton".equals(scope)) {
                // 3. 制造零件（创建对象）
                Object beanInstance = beanClass.getDeclaredConstructor().newInstance();

                // 4. 放入仓库（单例池）
                singletonObjects.put(beanName, beanInstance);
            }
            // 多例的现在不造，等需要时再造
        }
    }

    /**
     * 首先回顾一下：
     * （1）在实验一，我们已经完成了 bean 的扫描，将所有 classpath下标注了注解 @Component的 class 的信息构建出了 BeanDefination
     * 并且放到了 原材料集合 BeanDefinations 中。
     * （2）在实验二，我们读取原材料集合 BeanDefinations，根据每个 BeanDefination 的属性，产生出单例类的对象，我们称之为Bean，并将 Bean
     * 放到了 单例池 singletonObjects 中，这样我们就可以通过 getBean() 方法从 singletonObjects中取出单例对象。
     * 在这一过程中，我们不考虑懒加载， 从而保证只要是单例类的对象，一定在 singletonObjects中。
     * 提醒大家注意的是，在产生单例类的对象时，简单起见， 我们并没有对类中的基本类型的属性进行初始化。
     * 有能力的同学可以尝试定义 @Value注解进行初始化，这个过程不难。当然，类中的属性除了基本数据类型，还有引用类型。
     * 对于类中引用类型的属性，如何赋初值就比较麻烦。这也是实验三的核心目标。
     *
     * <p>
     * 因此，在实验三中，我们的目标只有一个，对类中的属性进行按 “属性的类型” 或者按 “对象的名字” 赋初值。
     * 即：根据类中属性对应的类型（属性仅标注了@Autowired注解），或者根据 @Qualifier的value值（标注了@Autowired+@Qualifier），
     * 从 singletonObjects 中找出对应的 Bean，并将值赋给该属性。
     * <p>
     * 核心算法逻辑：
     * *
     * 1. 遍历 beanDefinations，得到 每一个 beanDefination
     * 2. 根据 beanDefination 找到 clazz，再根据 clazz 找到所有的属性。遍历所有的属性，判断属性上有没有 @Autowired注解。
     * 2.1 如果没有，说明属性不需要初始化，直接跳出本轮循环，找下一个 beanDefination。
     * 2.2 如果有，说明属性需要注入。
     * 2.2.1 先根据 beanDefination对象的beanName，在 singletonObjects 中找到该Bean，然后对这个 Bean 赋初值，具体如下:
     * 2.2.2 如果属性上只有 Autowired 注解，那就是按照类型来注入。于是在 singletonObjects 中，在单例池中 找到和该属性类型一样的 bean，赋给该属性；
     * 2.2.3 如果属性标注了 Autowired  + Qualifier注解，那就是按名字注入，名字就是 @Qualifier的 value 值。在单例池中找到和该属性类型一样的 bean，赋给该属性     *
     * <p>
     * 备注：如何注入？
     * （1）可以构造函数注入。我给的代码中没有设置有参构造，这条路在本程序中行不通。
     * （2）可以通过setter注入。找到属性的名字，set + 首字母大写后，就找到对应的setter了，再用setter方法的invoke设置。
     * （3）暴力注入，调用属性的set方法，直接把属性值注入。注意调用前，要先将属性 setAccessible(true)。
     *
     * @param beanDefinations 原材料
     */

    private void autoWireObject(Set<BeanDefination> beanDefinations) {
        // 1. 遍历所有的BeanDefinition
        for (BeanDefination beanDefination : beanDefinations) {
            String beanName = beanDefination.getBeanName();
            Class<?> clazz = beanDefination.getBeanClass();

            // 2. 从单例池中获取当前bean的对象（只处理单例）
            Object bean = singletonObjects.get(beanName);
            if (bean == null) {
                continue; // 不是单例，跳过
            }

            // 3. 获取类的所有属性
            java.lang.reflect.Field[] fields = clazz.getDeclaredFields();

            // 4. 遍历所有属性
            for (java.lang.reflect.Field field : fields) {
                // 判断属性是否有@Autowired注解
                if (field.isAnnotationPresent(Autowired.class)) {
                    // 设置属性可访问（暴力注入）
                    field.setAccessible(true);

                    try {
                        // 判断是否有@Qualifier注解（按名字注入）
                        if (field.isAnnotationPresent(Qualifier.class)) {
                            // 按名字注入
                            Qualifier qualifier = field.getAnnotation(Qualifier.class);
                            String targetBeanName = qualifier.value();

                            // 从单例池中按名字查找
                            Object targetBean = singletonObjects.get(targetBeanName);
                            if (targetBean != null) {
                                // 注入属性
                                field.set(bean, targetBean);
                                System.out.println("按名字注入: " + beanName + "." + field.getName() +
                                        " -> " + targetBeanName);
                            } else {
                                throw new RuntimeException("找不到名为 '" + targetBeanName +
                                        "' 的Bean，无法注入到 " + beanName +
                                        "." + field.getName());
                            }
                        } else {
                            // 按类型注入
                            Class<?> fieldType = field.getType();
                            Object targetBean = null;

                            // 在单例池中查找类型匹配的Bean
                            for (Object candidate : singletonObjects.values()) {
                                if (fieldType.isAssignableFrom(candidate.getClass())) {
                                    targetBean = candidate;
                                    break;
                                }
                            }

                            if (targetBean != null) {
                                // 注入属性
                                field.set(bean, targetBean);
                                System.out.println("按类型注入: " + beanName + "." + field.getName() +
                                        " -> " + targetBean.getClass().getSimpleName());
                            } else {
                                throw new RuntimeException("找不到类型为 '" + fieldType.getName() +
                                        "' 的Bean，无法注入到 " + beanName +
                                        "." + field.getName());
                            }
                        }
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }
            }
        }
    }

    /**
     * 作用：根据 beanName，获得对象(不考虑 懒加载 )。
     * <p>
     * 算法描述：
     * 1. 根据入参 beanName 到singletonObjects中查。如果在 singletonObjects能查到，说明是单例，直接把查到的对象返回。
     * 2. 如果 singletonObjects中没有，说明不是单例（注意哈，不考虑懒加载的情况），需要遍历 BeanDefinations，找 beanName 对应
     * 的 Class 对象看是不是我们管理的bean。 如果是，临时产生一个对象返回，如果不是，说明 beanName 输错了或者压根不是我们框架管理的bean。
     * <p>
     * 具体步骤：
     * 2.1 如果能找到，产生一个对象就行返回就行。
     * 2.1.1 用 class对象的 getDeclaredConstructor().newInstance()产生 Bean 对象（此对象是多例的）
     * 2.1.2 return该对象，程序结束。
     * 2.2 如果找不到，说明入参 beanName写错了，或者压根不是 IoC容器管理的 Bean，直接抛出 NullPointerException,或者 return null。
     * 具体哪种方式，由你决定。
     *
     * @param beanName BeanDefinations中的存储的class对象的名字
     * @return 对象
     */
    public Object getBean(String beanName) {
        // 1. 先尝试从单例池中获取
        Object bean = singletonObjects.get(beanName);
        if (bean != null) {
            return bean;
        }

        // 2. 单例池中没有，说明可能不是单例，需要从BeanDefinitions中查找
        for (BeanDefination beanDefination : beanDefinations) {
            if (beanName.equals(beanDefination.getBeanName())) {
                try {
                    // 临时创建一个对象（多例）
                    Object newInstance = beanDefination.getBeanClass()
                            .getDeclaredConstructor()
                            .newInstance();
                    System.out.println("创建多例Bean: " + beanName);
                    return newInstance;
                } catch (Exception e) {
                    e.printStackTrace();
                    throw new RuntimeException("无法创建Bean: " + beanName, e);
                }
            }
        }

        // 3. 如果都找不到，抛出异常
        throw new RuntimeException("找不到名为 '" + beanName + "' 的Bean");
    }

}
